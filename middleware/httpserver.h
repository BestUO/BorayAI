#pragma once
#include <iostream>
#include <thread>
#include <cinatra.hpp>

class HttpServer
{
    public:
        HttpServer(std::string ip, std::string port, std::string topic,std::string middlewaredirpath, int pool_size=std::thread::hardware_concurrency());
        ~HttpServer() = default;

        void Run();
    private:
        cinatra::http_server __server;
        std::string __topic;
        std::string __middlewaredirpath;

        void __AddURL();
        void __URL_StyleTransfer_WCT_AdaIN();
        void __URL_StyleTransfer_Fast();
        void __URL_TextToSpeech_Fixed();

        void __AddMultiPartBegin(cinatra::request& req,std::string &name);
        bool __Begin_StyleTransfer_WCT_AdaIN(cinatra::request& req,std::string &name,std::string &dayname);
        bool __Begin_StyleTransfer_Fast(cinatra::request& req,std::string &name,std::string &dayname);
        bool __Begin_TextToSpeech_Fixed(cinatra::request& req,std::string &name,std::string &dayname);
        bool __Begin_StyleTransfer_Node(cinatra::request& req,std::string &name,std::string &dayname);
};