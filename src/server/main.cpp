#include "message.pb.h"

#include "AccessLayer.hpp"

#include <zmq.hpp>
#include <iostream>
#include <stdlib.h>
#include <unistd.h>
#include <string.h>
#include <time.h>

// Main server entry point
int main(int argc, char *argv[])
{
    // Verify protobuf version
    GOOGLE_PROTOBUF_VERIFY_VERSION;

    // Prepare context and publisher
    zmq::context_t context(1);
    zmq::socket_t  socket(context, ZMQ_REP);
    socket.bind("tcp://*:5555");

    // Wait for requests
    while (1)
    {   
        // Create 0MQ request
        zmq::message_t request;

        // Receive request from client
        socket.recv(&request);

        // Create Message object
        Request message;

        // Deserialise message
        std::string msg_str(static_cast<char *>(request.data()), request.size());
        message.ParseFromString(msg_str);

        Reply replyMessage;

        // Switch on request type
        switch(message.command())
        {
            // Connect to board
            case Request::CONNECT:
            {
                std::cout << "Received connect request" << std::endl;

                // Call library connectBoard
                ID id = connectBoard(message.ip().c_str(), message.port());

                // Check if call failed
                if (id > 0)
                {
                    replyMessage.set_result(Reply::SUCCESS);
                    replyMessage.set_id(id);
                }
                else
                {
                    replyMessage.set_result(Reply::FAILURE);
                    replyMessage.set_id(id);
                }

                // Done
                break;
            }

            // Disconnect from board
            case Request::DISCONNECT:
            {
                std::cout << "Received disconnect request" << std::endl;

                // Call library disconnectBoard
                ERROR err = disconnectBoard(message.id());
            
                // Check if call failed and send result
                if (err == SUCCESS)
                    replyMessage.set_result(Reply::SUCCESS);
                else
                    replyMessage.set_result(Reply::FAILURE);

                // Done
                break;
            }

            // Reset board
            case Request::RESET_BOARD:
            {
                std::cout << "Received reset board request" << std::endl;

                // NOTE: Not implemented yet, reply with dummy value
                replyMessage.set_result(Reply::SUCCESS);

                // Done
                break;
            }

            case Request::GET_STATUS:
            {
                std::cout << "Received get status request" << std::endl;

                // NOTE: Not implemented yet, reply with dummy value
                replyMessage.set_result(Reply::SUCCESS);
                replyMessage.set_status(Reply::OK);

                // Done
                break;                
            }

            // Get register list
            case Request::GET_REGISTER_LIST:
            {
                std::cout << "Received get register list request" << std::endl;

                // Call library function
                unsigned int num_registers;
                REGISTER_INFO *list = getRegisterList(message.id(), &num_registers);

                // Check if any registers available (or call failed)
                if (num_registers == 0 || list == NULL)
                    replyMessage.set_result(Reply::FAILURE);
                else
                {                       
                    // Set result type
                    replyMessage.set_result(Reply::SUCCESS);

                    // Register found, create register list
                    for(unsigned i = 0; i < num_registers; i++)
                    {
                        // Create new RegisterInfoType instance
                        Reply::RegisterInfoType *regInfo = replyMessage.add_registerlist();

                        regInfo -> set_name(list[i].name);               
                        regInfo -> set_size(list[i].size);
                        regInfo -> set_description(list[i].description);

                        // Convert permission enum
                        if (list[i].permission == READ)
                            regInfo -> set_permission(Reply::READ);
                        else if (list[i].permission == WRITE)
                            regInfo -> set_permission(Reply::WRITE);
                        else
                            regInfo -> set_permission(Reply::READWRITE);

                        // Convert register type enum
                        if (list[i].type == SENSOR)
                            regInfo -> set_type(Reply::SENSOR);
                        else if (list[i].type == BOARD_REGISTER)
                            regInfo -> set_type(Reply::BOARD_REGISTER);
                        else
                            regInfo -> set_type(Reply::FIRMWARE_REGISTER);

                        // Convert device type enum
                        if (list[i].device == BOARD)
                            regInfo -> set_device(Reply::BOARD);
                        else if (list[i].device == FPGA_1)
                            regInfo -> set_device(Reply::FPGA_1);
                        else if (list[i].device == FPGA_2)
                            regInfo -> set_device(Reply::FPGA_2);                       
                    }
                }

                // Free up memory
                free(list);

                // All done
                break;
            }

            // Get register value
            case Request::GET_REGISTER_VALUE:
            {
                std::cout << "Received get register value request" << std::endl;

                // Extract enums
                DEVICE dev;
                if (message.device() == Request::BOARD)
                    dev = BOARD;
                else if (message.device() == Request::FPGA_1)
                    dev = FPGA_1;
                else if (message.device() == Request::FPGA_2)
                    dev = FPGA_2;

                // Call library function
                REGISTER regName = message.registername().c_str();
                VALUES vals = readRegister(message.id(), dev, regName, 1);

                // Check if call succeeded
                if (vals.error == FAILURE)
                    replyMessage.set_result(Reply::FAILURE);
                else
                {
                    replyMessage.set_result(Reply::SUCCESS);
                    replyMessage.set_value(vals.values[0]);
                }

                // Done
                break;
            }

            // Get register value
            case Request::GET_REGISTER_VALUES:
            {
                std::cout << "Received get register values request" << std::endl;

                // Extract enums
                DEVICE dev;
                if (message.device() == Request::BOARD)
                    dev = BOARD;
                else if (message.device() == Request::FPGA_1)
                    dev = FPGA_1;
                else if (message.device() == Request::FPGA_2)
                    dev = FPGA_2;

                // Call library function
                REGISTER regName = message.registername().c_str();
                VALUES vals = readRegister(message.id(), dev, regName, message.n());

                // Check if call succeeded
                if (vals.error == FAILURE)
                    replyMessage.set_result(Reply::FAILURE);
                else
                {
                    // Set values and success
                    for(unsigned i = 0; i < message.n(); i++)
                        replyMessage.add_values(vals.values[i]);
                    replyMessage.set_result(Reply::SUCCESS);
                }

                // Done
                break;
            }

            case Request::SET_REGISTER_VALUE:
            {
                std::cout << "Received set register value request" << std::endl;

                // Extract enums
                DEVICE dev;
                if (message.device() == Request::BOARD)
                    dev = BOARD;
                else if (message.device() == Request::FPGA_1)
                    dev = FPGA_1;
                else if (message.device() == Request::FPGA_2)
                    dev = FPGA_2;

                // Call library function
                REGISTER regName = message.registername().c_str();
                uint32_t value = message.value();
                ERROR err = writeRegister(message.id(), dev, regName, 1, &value);

                // Check if call succeeded
                if (err == FAILURE)
                    replyMessage.set_result(Reply::FAILURE);
                else
                    replyMessage.set_result(Reply::SUCCESS);

                // Done
                break;
            }

            case Request::SET_REGISTER_VALUES:
            {
                std::cout << "Received set register values request" << std::endl;

                // Extract enums
                DEVICE dev;
                if (message.device() == Request::BOARD)
                    dev = BOARD;
                else if (message.device() == Request::FPGA_1)
                    dev = FPGA_1;
                else if (message.device() == Request::FPGA_2)
                    dev = FPGA_2;

                // Call library function
                REGISTER regName = message.registername().c_str();
                ERROR err = writeRegister(message.id(), dev, regName, message.n(), 
                                          message.mutable_values() -> mutable_data());

                // Check if call succeeded
                if (err == FAILURE)
                    replyMessage.set_result(Reply::FAILURE);
                else
                    replyMessage.set_result(Reply::SUCCESS);

                // Done
                break;
            }

            // Load firmware blocking
            case Request::LOAD_FIRMWARE_BLOCKING:
            {
                std::cout << "Received load firmware blocking request" << std::endl;

                // Convert device type
                DEVICE dev;
                if (message.device() == Request::BOARD)
                    dev = BOARD;
                else if (message.device() == Request::FPGA_1)
                    dev = FPGA_1;
                else if (message.device() == Request::FPGA_2)
                    dev = FPGA_2;
    
                std::cout << "ID: " << message.id() << ", file: " << message.file() << std::endl;

                ERROR err = loadFirmwareBlocking(message.id(), dev,
                                                "/home/lessju/MemoryMap.xml");
//                                                 message.file().c_str());

                // Check if call failed and send result
                if (err == SUCCESS)
                    replyMessage.set_result(Reply::SUCCESS);
                else
                    replyMessage.set_result(Reply::FAILURE);

                // Done
                break;
            }

            // Load firmware
            case Request::LOAD_FIRMWARE:
            {
                std::cout << "Received load firmware request" << std::endl;

                // Convert device type
                DEVICE dev;
                if (message.device() == Request::BOARD)
                    dev = BOARD;
                else if (message.device() == Request::FPGA_1)
                    dev = FPGA_1;
                else if (message.device() == Request::FPGA_2)
                    dev = FPGA_2;
    
                std::cout << "ID: " << message.id() << ", file: " << message.file() << std::endl;

                ERROR err = loadFirmwareBlocking(message.id(), dev,
                                                 "/home/lessju/MemoryMap.xml");
//                                                 message.file().c_str());

                // Check if call failed and send result
                if (err == SUCCESS)
                    replyMessage.set_result(Reply::SUCCESS);
                else
                    replyMessage.set_result(Reply::FAILURE);

                // Done
                break;
            }

            default:
                std::cout << "Unsupported command" << std::endl;
        }
        
        // Serialise message
        std::string replyString;
        replyMessage.SerializeToString(&replyString);

        // Send reply back to client
        zmq::message_t reply(replyString.size());
        memcpy((void *) reply.data(), replyString.c_str(), replyString.size());
        socket.send(reply);

        printf("Sent reply to client\n");
    }

    return 0;
}

