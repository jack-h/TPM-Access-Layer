#include <zmq.hpp>
#include <iostream>
#include <stdlib.h>
#include <unistd.h>
#include <string.h>
#include <time.h>

#include "AccessLayer.hpp"
#include "utils.hpp"

#include "message.pb.h"

// --------------------- REQUEST HANDLING FUNCTIONS ------------------------

// Process connect to board request
void processConnectBoard(Request *message, Reply *replyMessage)
{
    std::cout << "Received connect request to " << message -> ip()  << std::endl;

    // Call library connectBoard
    ID id = connectBoard(message -> ip().c_str(), message -> port());

    // TEMPORARY: Load firmware
    loadFirmwareBlocking(id, FPGA_1, "/home/lessju/map.xml");

    // Check if call failed
    if (id > 0)
    {
        replyMessage -> set_result(Reply::SUCCESS);
        replyMessage -> set_id(id);
    }
    else
        replyMessage -> set_result(Reply::FAILURE);
}

// Process disconnect from board request
void processDisconnectBoard(Request *message, Reply *replyMessage)
{
    std::cout << "Received disconnect request" << std::endl;

    // Call library disconnectBoard
    RETURN err = disconnectBoard(message -> id());

    // Check if call failed and send result
    replyMessage -> set_result(convertErrorEnum(err));
}

// Process get register list request
void processGetRegisterList(Request *message, Reply *replyMessage)
{
    std::cout << "Received get register list request" << std::endl;

    // Call library function
    unsigned int num_registers;
    REGISTER_INFO *list = getRegisterList(message -> id(), &num_registers);

    // Check if any registers available (or call failed)
    if (num_registers == 0 || list == NULL)
        replyMessage -> set_result(Reply::FAILURE);
    else
    {                       
        // Set result type
        replyMessage -> set_result(Reply::SUCCESS);

        // Register found, create register list
        for(unsigned i = 0; i < num_registers; i++)
        {
            // Create new RegisterInfoType instance and populate
            Reply::RegisterInfoType *regInfo = replyMessage -> add_registerlist();
            regInfo -> set_name(list[i].name);               
            regInfo -> set_size(list[i].size);
            regInfo -> set_description(list[i].description);
            regInfo -> set_permission(convertPermissionEnum(list[i].permission));
            regInfo -> set_type(convertTypeEnum(list[i].type));
            regInfo -> set_device(convertDeviceEnum(list[i].device));
        }
    }

    // Free up memory
    free(list);
}

// Process get register value request
void processGetRegisterValue(Request *message, Reply *replyMessage)
{
    std::cout << "Received get register value request" << std::endl;

    // Extract enums
    DEVICE dev = convertDeviceEnum(message -> device());

    // Call library function
    REGISTER regName = message -> registername().c_str();
    VALUES vals = readRegister(message -> id(), dev, regName, 1);

    // Check if call succeeded
    if (vals.error == FAILURE)
        replyMessage -> set_result(Reply::FAILURE);
    else
    {
        replyMessage -> set_result(Reply::SUCCESS);
        replyMessage -> set_value(vals.values[0]);
    }
}

// Process get register values request
void processGetRegisterValues(Request *message, Reply *replyMessage)
{
    std::cout << "Received get register values request" << std::endl;

    // Extract enum
    DEVICE dev = convertDeviceEnum(message -> device());

    // Call library function
    REGISTER regName = message -> registername().c_str();
    VALUES vals = readRegister(message -> id(), dev, regName, message -> n());

    // Check if call succeeded
    if (vals.error == FAILURE)
        replyMessage -> set_result(Reply::FAILURE);
    else
    {
        // Set values and success
        for(unsigned i = 0; i < message -> n(); i++)
            replyMessage -> add_values(vals.values[i]);
        replyMessage -> set_result(Reply::SUCCESS);
    }
}

// Process set register value request
void processSetRegisterValue(Request *message, Reply *replyMessage)
{
    std::cout << "Received set register value request" << std::endl;

    // Extract enums
    DEVICE dev = convertDeviceEnum(message -> device());

    // Call library function
    REGISTER regName = message -> registername().c_str();
    uint32_t value = message -> value();
    RETURN err = writeRegister(message -> id(), dev, regName, 1, &value);

    // Check if call succeeded
    replyMessage -> set_result(convertErrorEnum(err));
}

// Process set register values request
void processSetRegisterValues(Request *message, Reply *replyMessage)
{
    std::cout << "Received set register values request" << std::endl;

    // Extract enums
    DEVICE dev = convertDeviceEnum(message -> device());

    // Call library function
    REGISTER regName = message -> registername().c_str();
    RETURN err = writeRegister(message -> id(), dev, regName, message -> n(), 
                              message -> mutable_values() -> mutable_data());

    // Check if call succeeded
    replyMessage -> set_result(convertErrorEnum(err));
}

// Process load firmware blocking
void processLoadFirmwareBlocking(Request *message, Reply *replyMessage)
{
    std::cout << "Received load firmware blocking request" << std::endl;

    // Convert device type
    DEVICE dev = convertDeviceEnum(message -> device());

    std::cout << "ID: " << message -> id() << ", file: " << message -> file() << std::endl;

    RETURN err = loadFirmwareBlocking(message -> id(), dev,
                                     "/home/lessju/map.xml");
                                    // message -> file().c_str());

    // Check if call failed and send result
    replyMessage -> set_result(convertErrorEnum(err));
}

// Process load firmware
void processLoadFirmware(Request *message, Reply *replyMessage)
{
    std::cout << "Received load firmware request" << std::endl;

    // Convert device type
    DEVICE dev = convertDeviceEnum(message -> device());

    std::cout << "ID: " << message -> id() << ", file: " << message -> file() << std::endl;

    RETURN err = loadFirmwareBlocking(message -> id(), dev,
                                     "/home/lessju/map.xml");
//                                     message -> file().c_str());

    // Check if call failed and send result
    replyMessage -> set_result(convertErrorEnum(err));
}

// ------------------------------------------------------------------------

// 0MQ Connection string
std::string connectionString("tcp://*:5555");

// Main server entry point
int main(int argc, char *argv[])
{
    // Verify protobuf version
    GOOGLE_PROTOBUF_VERIFY_VERSION;

    // Prepare context and publisher
    zmq::context_t context(1);
    zmq::socket_t  socket(context, ZMQ_REP);
    socket.bind(connectionString.c_str());

    // Wait for requests
    while (true)
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
                processConnectBoard(&message, &replyMessage);
                break;
            }

            // Disconnect from board
            case Request::DISCONNECT:
            {
                processDisconnectBoard(&message, &replyMessage);
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

            // Get board status
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
                processGetRegisterList(&message, &replyMessage);
                break;
            }

            // Get register value
            case Request::GET_REGISTER_VALUE:
            {
                processGetRegisterValue(&message, &replyMessage);
                break;
            }

            // Get register values
            case Request::GET_REGISTER_VALUES:
            {
                processGetRegisterValues(&message, &replyMessage);
                break;
            }

            // Set reigtser value
            case Request::SET_REGISTER_VALUE:
            {
                processSetRegisterValue(&message, &replyMessage);
                break;
            }

            // Set register values
            case Request::SET_REGISTER_VALUES:
            {
                processSetRegisterValues(&message, &replyMessage);
                break;
            }

            // Load firmware blocking
            case Request::LOAD_FIRMWARE_BLOCKING:
            {
                processLoadFirmwareBlocking(&message, &replyMessage);
                break;
            }

            // Load firmware
            case Request::LOAD_FIRMWARE:
            {
                processLoadFirmware(&message, &replyMessage);
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
