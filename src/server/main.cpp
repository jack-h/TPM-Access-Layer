#include <zmq.hpp>
#include <stdlib.h>
#include <unistd.h>
#include <string.h>
#include <time.h>

#include <iostream>
#include <string>

#include "ChannelisedDataReader.h"
#include "AccessLayer.hpp"
#include "utils.hpp"

#include "message.pb.h"

#include <google/protobuf/io/zero_copy_stream_impl_lite.h>
#include <google/protobuf/io/coded_stream.h>

// Structure for handling signed 8-bit data 
struct Complex
{
    signed char real;
    signed char imag;
};

// ---- GLOBAL - Ghax Hekk --------------------

// 0MQ Connection string
std::string connectionString("tcp://*:5555");

// Prepare context and publisher
zmq::context_t context(1);
zmq::socket_t  socket(context, ZMQ_REP);

// XML and Data files directories
std::string data_directory = "/home/lessju/Code/AAVS/aavs_daq/python/";
std::string xml_directory = "/home/lessju/Code/TPM-Access-Layer/src/server/xml/";

// Channelised data reader for reading channel data hdf5
ChannelisedDataReader *reader;

// Number of channels
unsigned nof_chans = 512;

// --------------------- REQUEST HANDLING FUNCTIONS ------------------------

// Process connect to board request
void processConnectBoard(Request *message, Reply *replyMessage)
{
    std::cout << "Received connect request to " << message -> ip()  << std::endl;

    // Call library connectBoard
    BOARD_MAKE board = convertBoardEnum(message -> board());
    ID id = connectBoard(board, message -> ip().c_str(), message -> port());

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
    REGISTER_INFO *list = getRegisterList(message -> id(), &num_registers, true);

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
            regInfo -> set_value(list[i].value);
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
    RETURN err = writeRegister(message -> id(), dev, regName, &value, 1, 0);

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
    RETURN err = writeRegister(message -> id(), dev, regName,
                              message -> mutable_values() -> mutable_data(),
                              message -> n(), 0);

    // Check if call succeeded
    replyMessage -> set_result(convertErrorEnum(err));
}

// Process load firmware
void processLoadFirmware(Request *message, Reply *replyMessage)
{
    std::cout << "Received load firmware request " << message -> device() << std::endl;

    // Convert device type
    DEVICE dev = convertDeviceEnum(message -> device());

    RETURN err;
    switch(dev)
    {
        case BOARD:
        {
            printf("Get board registers\n");
            err = loadFirmware(message -> id(), dev,
                                      "/opt/aavs/firmware_xml/cpld.xml");
            break;
        }
        case FPGA_1:
        {
            printf("Get fpga1 registers\n");
            err = loadFirmware(message -> id(), dev,
                                      "/opt/aavs/firmware_xml/fpga.xml");
            break;
        }
        case FPGA_2:
        {
            printf("Get fpga2 registers\n");
            err = loadFirmware(message -> id(), dev,
                                      "/opt/aavs/firmware_xml/fpga.xml", 0x10000000);
            break;
        }
        default:
        {
            printf("Invalid device\n");
            err = FAILURE;
        }
    }


    // Check if call failed and send result
    replyMessage -> set_result(convertErrorEnum(err));
}

void processGetChannelisedData(Request *message)
{
    std::cout << "Received get channelised data request" << std::endl;
    
    // Get channelised data request message from request
    ChannelisedDataRequest *dataRequest = message -> mutable_channeliseddatarequest();

    size_t buffer_size = nof_chans * dataRequest->samplecount() * 2 * (sizeof(Complex) + 16);
    unsigned char *buffer = (unsigned char *) malloc(buffer_size);

    google::protobuf::io::ArrayOutputStream *arrayStream = new
            google::protobuf::io::ArrayOutputStream(buffer, (int) buffer_size);
    google::protobuf::io::CodedOutputStream *codedOutput =
            new google::protobuf::io::CodedOutputStream(arrayStream);

    if (0)
    {
        complex_t *c_buffer = (complex_t *) malloc(dataRequest -> samplecount() * nof_chans * sizeof(complex_t));
        reader = new ChannelisedDataReader("/home/lessju/Code/AAVS/aavs_daq/python/channel_data.hdf5");
        for(unsigned i = 0; i < 16; i++)
            if (reader->getData(c_buffer, i, 0, dataRequest->samplecount(), nof_chans))
            {
                printf("Infaqa haqq alla\n");
            }
            else
            {
                printf("woohoo\n");
            }

    }

    // Send a message per channel (Pol X)
    for(unsigned i = 0; i < nof_chans; i++)
    {
        ChannelisedDataResponse *replyMessage = new ChannelisedDataResponse;

        // Compose reply message
        replyMessage -> set_antennaid(dataRequest -> antennaid());
        replyMessage -> set_pol(ChannelisedDataResponse::X);
        replyMessage -> set_samplecount(dataRequest -> samplecount());
        replyMessage -> set_bitspersample(8);
        
        for(int j = 0; j < dataRequest -> samplecount(); j++)
        {
            // Create new RegisterInfoType instance and populate
            ChannelisedDataResponse::ComplexSignedInt *value = replyMessage -> add_csi();
            value -> set_real((uint8_t) i);
            value -> set_imaginary((uint8_t) j);
        }

        codedOutput -> WriteLittleEndian32((uint32_t) replyMessage -> ByteSize());
        replyMessage -> SerializeToCodedStream(codedOutput);

        delete replyMessage;
   }

    // Send a message per channel (Pol Y)
    for(unsigned i = 0; i < nof_chans; i++)
    {
        ChannelisedDataResponse *replyMessage = new ChannelisedDataResponse;

        // Compose reply message
        replyMessage -> set_antennaid(dataRequest -> antennaid());
        replyMessage -> set_pol(ChannelisedDataResponse::Y);
        replyMessage -> set_samplecount(dataRequest -> samplecount());
        replyMessage -> set_bitspersample(8);

        for(int j = 0; j < dataRequest -> samplecount(); j++)
        {
            // Create new RegisterInfoType instance and populate
            ChannelisedDataResponse::ComplexSignedInt *value = replyMessage -> add_csi();
            value -> set_real((uint8_t) i);
            value -> set_imaginary((uint8_t) j);
        }

        codedOutput -> WriteLittleEndian32((uint32_t) replyMessage -> ByteSize());
        replyMessage -> SerializeToCodedStream(codedOutput);

        delete replyMessage;
    }

    // Send reply back to client
    zmq::message_t reply((size_t) codedOutput -> ByteCount());
    memcpy(reply.data(), buffer, (size_t) codedOutput -> ByteCount());
    socket.send(reply);

    // Free up buffer
    delete codedOutput;
    delete arrayStream;
    free(buffer);
}

void processGetRawData(Request *message, Reply *reply)
{
}

// ------------------------------------------------------------------------

// Main server entry point
int main(int argc, char *argv[])
{
    // Verify protobuf version
    GOOGLE_PROTOBUF_VERIFY_VERSION;

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
        bool sendReply = true;
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

            // Load firmware
            case Request::LOAD_FIRMWARE:
            {
                processLoadFirmware(&message, &replyMessage);
                break;
            }

            // Raw Data request
            case Request::GET_CHANNELISED_DATA:
            {
                processGetChannelisedData(&message);
                sendReply = false;
                break;
            }

            case Request::GET_RAW_DATA:
            {
                processGetRawData(&message, &replyMessage);
                break;
            }

            default:
                std::cout << "Unsupported command" << std::endl;
        }
        
        if (sendReply)
        {
            std::string replyString;

            // Serialise message
            replyMessage.SerializeToString(&replyString);

            // Send reply back to client
            zmq::message_t reply(replyString.size());
            memcpy(reply.data(), replyString.c_str(), replyString.size());
            socket.send(reply);

            printf("Sent reply to client\n");
        }

        sendReply = true;
    }
}
