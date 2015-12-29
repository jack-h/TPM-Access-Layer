#include <zmq.hpp>
#include <stdlib.h>
#include <unistd.h>
#include <string.h>
#include <time.h>

#include <iostream>
#include <string>

#include "hdf5/ChannelFormatFileManager.h"
#include "hdf5/FileModes.h"
#include "hdf5/RawFormatFileManager.h"
#include "AccessLayer.hpp"
#include "utils.hpp"

#include "message.pb.h"

#include <google/protobuf/io/zero_copy_stream_impl_lite.h>
#include <google/protobuf/io/coded_stream.h>
#include <hdf5/ChannelFormatFileManager.h>

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
std::string data_directory = "/data";
std::string xml_directory = "/home/lessju/Code/TPM-Access-Layer/src/server/xml/";

// Data readers
ChannelFormatFileManager channelDataReader = ChannelFormatFileManager(data_directory, FileModes::READ);
RawFormatFileManager     rawDataReader     = RawFormatFileManager(data_directory, FileModes::READ);

// Number of channels
unsigned nof_antennas = 16;
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

        // If we are connecting to a ROACH board, then we also include the list of available firmware
        if (board == ROACH_BOARD || board == ROACH2_BOARD)
        {
            // Get list of firmware from the board
            uint32_t num_firmware;
            FIRMWARE firmware = getFirmware(id, BOARD, &num_firmware);
            for(unsigned i = 0; i < num_firmware; i++)
                replyMessage->add_firmware(firmware[i]);
        }
    }
    else
    {
        replyMessage->set_result(Reply::FAILURE);
        replyMessage->set_status(Reply::NETWORK_ERROR);
    }
}

// Process disconnect from board request
void processDisconnectBoard(Request *message, Reply *replyMessage)
{
    std::cout << "Received disconnect request" << std::endl;

    // Call library disconnectBoard
    RETURN err = disconnectBoard(message -> id());

    // Updates status
    if (message->id() == 0)
        replyMessage->set_status(Reply::NOT_CONNECTED);
    else
        replyMessage->set_status(convertTpmStatus(getStatus(message -> id())));

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
        replyMessage->set_result(Reply::FAILURE);
    else
    {                       
        // Set result type
        replyMessage -> set_result(Reply::SUCCESS);
        printf("Found %d registers\n", num_registers);

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

    // Update with board status
    replyMessage->set_status(convertTpmStatus(getStatus(message -> id())));

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

    // Update with board status
    replyMessage->set_status(convertTpmStatus(getStatus(message -> id())));
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

    // Update with board status
    replyMessage->set_status(convertTpmStatus(getStatus(message -> id())));
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

    // Update with board status
    replyMessage->set_status(convertTpmStatus(getStatus(message -> id())));
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

    // Update with board status
    replyMessage->set_status(convertTpmStatus(getStatus(message -> id())));
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
                                      "xml/cpld.xml");
            break;
        }
        case FPGA_1:
        {
            printf("Get fpga1 registers\n");
            err = loadFirmware(message -> id(), dev,
                                      "xml/fpga.xml");
            break;
        }
        case FPGA_2:
        {
            printf("Get fpga2 registers\n");
            err = loadFirmware(message -> id(), dev,
                                      "xml/fpga.xml", 0x10000000);
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

    // Update with board status
    replyMessage->set_status(convertTpmStatus(getStatus(message -> id())));
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

    // Read data form latest file
    // All channels, one polarisations, requested antenna, requested sample count
    int antennas[1] = { dataRequest->antennaid() };
    int *channels = (int *) malloc(nof_chans * sizeof(int));
    int pol[1] = { 0 };
    for(unsigned i = 0; i < nof_chans; i++) channels[i] = i;
    complex16_t *channel_data = channelDataReader.read_data("", channels, antennas, pol, dataRequest -> samplecount(), 0);

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
            value -> set_real((uint8_t) (channel_data + i * dataRequest-> samplecount() + j)->real);
            value -> set_imaginary((uint8_t) (channel_data + i * dataRequest-> samplecount() + j)->imag);
        }

        codedOutput -> WriteLittleEndian32((uint32_t) replyMessage -> ByteSize());
        replyMessage -> SerializeToCodedStream(codedOutput);

        delete replyMessage;
    }
    free(channel_data);

    // Read data form latest file
    // All channels, one polarisations, requested antenna, requested sample count
    pol[0] = 1;
    channel_data = channelDataReader.read_data("", channels, antennas, pol, dataRequest -> samplecount(), 0);

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
            value -> set_real((uint8_t) (channel_data + i * dataRequest-> samplecount() + j)->real);
            value -> set_imaginary((uint8_t) (channel_data + i * dataRequest-> samplecount() + j)->imag);
        }

        codedOutput -> WriteLittleEndian32((uint32_t) replyMessage -> ByteSize());
        replyMessage -> SerializeToCodedStream(codedOutput);

        delete replyMessage;
    }

    // Send reply back to client
    zmq::message_t reply((size_t) codedOutput -> ByteCount());
    memcpy(reply.data(), buffer, (size_t) codedOutput -> ByteCount());
    socket.send(reply);

    // Free up buffers and delete objects
    delete codedOutput;
    delete arrayStream;

    free(channel_data);
    free(channels);
    free(buffer);
}

void processGetRawData(Request *message, Reply *reply)
{
    std::cout << "Received get antenna data request" << std::endl;

    // Get channelised data request message from request
    RawDataRequest *dataRequest = message -> mutable_rawdatarequest();

    // Get pointer to reply object
    Reply::RawDataReply *raw_data_reply = reply -> mutable_rawdata();

    // Get data from file
    int antennas[16] = {0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15};
    int pols[2] = {0, 1};
    int8_t *raw_data = rawDataReader.read_data("", antennas, pols, dataRequest->samplecount(), 0);

    // Loop over antennas
    for(unsigned i = 0; i < nof_antennas; i++ )
    {
        // Add X part
        Reply::RawDataReply::AdcPower *power = raw_data_reply->add_adcchannels();
        for(unsigned j = 0; j < dataRequest->samplecount(); j++)
            power->add_powersamples(raw_data[i * 2 * dataRequest->samplecount() + j]);

        // Add Y part
        power = raw_data_reply->add_adcchannels();
        for(unsigned j = 0; j < dataRequest->samplecount(); j++)
            power->add_powersamples(raw_data[(i * 2 + 1) * dataRequest->samplecount() + j]);
    }

    reply->set_result(Reply::SUCCESS);
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
