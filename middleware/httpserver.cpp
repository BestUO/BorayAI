#include "httpserver.h"
#include <iostream>
#include "RWSeparate.hpp"
#include <glog/logging.h>

HttpServer::HttpServer(std::string ip, std::string port,std::string topic,std::string middlewaredirpath, int pool_size):
                                    __server(pool_size),__topic(topic),__middlewaredirpath(middlewaredirpath)
{
    __server.listen(ip, port);
    __server.set_upload_dir(middlewaredirpath.substr(0,middlewaredirpath.size()-1));
    __server.set_multipart_begin([this](cinatra::request& req,std::string &name)
    {
        this->__AddMultiPartBegin(req, name);
    });
    __server.set_upload_check([this](cinatra::request& req, cinatra::response &res)
    {
        if(req.get_content_type() != cinatra::content_type::multipart)
            return false;
        return true;
    });
    __AddURL();
}

void HttpServer::Run()
{
    __server.run();
}

void HttpServer::__AddURL()
{
    __URL_StyleTransfer_WCT_AdaIN();
    __URL_StyleTransfer_Fast();
    __URL_TextToSpeech_Fixed();
}

void HttpServer::__AddMultiPartBegin(cinatra::request& req,std::string &name)
{
    auto create_dir = [this]()
    {
        auto tt = std::chrono::system_clock::to_time_t(std::chrono::system_clock::now());
        struct tm* ptm = localtime(&tt);
        char date[20] = { 0 };
        sprintf(date, "%d%02d%02d/", (int)ptm->tm_year + 1900, (int)ptm->tm_mon + 1, (int)ptm->tm_mday);
        std::string dirpath = this->__middlewaredirpath + std::string(date);
	    std::filesystem::create_directories(dirpath);
        return std::string(date);
    };
    std::string dayname = create_dir();
    if(__Begin_StyleTransfer_WCT_AdaIN(req, name, dayname))
        return;
    if(__Begin_StyleTransfer_Fast(req, name, dayname))
        return;
    if(__Begin_TextToSpeech_Fixed(req, name, dayname))
        return;
    __Begin_StyleTransfer_Node(req, name, dayname);
}

bool HttpServer::__Begin_StyleTransfer_WCT_AdaIN(cinatra::request& req,std::string &name,std::string &dayname)
{
    if(req.get_url() == "/StyleTransfer/WCTAdaIN")
    {
        auto key = req.get_multipart_field_name("name");
        std::string lastname("-style.jpg_ing");
        if(key.find("contentphoto") != std::string::npos)
            lastname = "-content.jpg_ing";

        if(req.get_uuid().empty())
            req.set_uuid(RWSeparate<cinatra::http_server::type>::inst().GetUUID());
        
        name = dayname + __topic + "-" + req.get_uuid() + lastname;
        return true;
    }
    return false;
}

bool HttpServer::__Begin_StyleTransfer_Fast(cinatra::request& req,std::string &name,std::string &dayname)
{
    if(req.get_url() == "/StyleTransfer/Fast")
    {
        std::string lastname("-content.jpg_ing");

        if(req.get_uuid().empty())
            req.set_uuid(RWSeparate<cinatra::http_server::type>::inst().GetUUID());
        
        name = dayname + __topic + "-" + req.get_uuid() + lastname;
        return true;
    }
    return false;
}

bool HttpServer::__Begin_TextToSpeech_Fixed(cinatra::request& req,std::string &name,std::string &dayname)
{
    if(req.get_url() == "/TextToSpeech/Fixed")
    {
        if(req.get_uuid().empty())
            req.set_uuid(RWSeparate<cinatra::http_server::type>::inst().GetUUID());
        return true;
    }
    return false;
}

bool HttpServer::__Begin_StyleTransfer_Node(cinatra::request& req,std::string &name,std::string &dayname)
{
    name = dayname + __topic + "-" + req.get_uuid() + "-content.jpg_ing";
    return true;
}

void HttpServer::__URL_StyleTransfer_WCT_AdaIN()
{
    auto fun = [this](cinatra::request& req, cinatra::response& res) 
    {
        LOG(INFO) << "request " << req.get_uuid() << " already recved files";
        if(req.get_upload_files().size() != 2 || req.get_multipart_value_by_key1("modelname").empty() || 
                req.get_multipart_value_by_key1("alpha").empty())
        {
            res.set_delay(false);
            res.set_status_and_content(cinatra::status_type::ok, "params lost");
            LOG(INFO) << "params lost";
            return;
        }

        auto genmessage = [](cinatra::request& req, const std::string &alpha, const std::string &middlewaredirpath)
        {
            //StyleTransferm-WCT_1234568_20210402/192168001007-1234568-content.jpg:20210402/192168001007-1234568-style.jpg:0.8_192168001007
            auto& files = req.get_upload_files();
            std::string filename1 = files[0].get_file_path().substr(middlewaredirpath.size());
            std::string filename2 = files[1].get_file_path().substr(middlewaredirpath.size());
            if(filename1.find("-content.jpg") != std::string::npos)
                return filename1 + ":" + filename2 + ":" + alpha;
            else
                return filename2 + ":" + filename1 + ":" + alpha;
        };
        res.set_delay(true);
        // res.set_status_and_content(cinatra::status_type::ok, "multipart finished");

        std::string modelname = req.get_multipart_value_by_key1("modelname");
        std::string alpha = req.get_multipart_value_by_key1("alpha");
        std::string message = genmessage(req, alpha, this->__middlewaredirpath);
        message = modelname + "_" + req.get_uuid() + "_" + message + "_" + this->__topic;
        auto con = req.get_conn<cinatra::http_server::type>();
        RWSeparate<cinatra::http_server::type>::inst().Add2Map(con, req.get_uuid());
        SimpleWrapKafka::inst().Add2Kafka(modelname, message);
        
        LOG(INFO) << "request " << req.get_uuid() << " already add kafka:" << message;
    };
    __server.set_http_handler<cinatra::GET, cinatra::POST>("/StyleTransfer/WCTAdaIN", fun);
}

void HttpServer::__URL_StyleTransfer_Fast()
{
    auto fun = [this](cinatra::request& req, cinatra::response& res) 
    {
        LOG(INFO) << "request " << req.get_uuid() << " already recved files";
        if(req.get_upload_files().size() != 1 || req.get_multipart_value_by_key1("modelname").empty() || 
                req.get_multipart_value_by_key1("stylename").empty())
        {
            res.set_delay(false);
            res.set_status_and_content(cinatra::status_type::ok, "params lost");
            LOG(INFO) << "params lost";
            return;
        }
        auto fun = [](cinatra::request& req, const std::string &alpha, const std::string &middlewaredirpath)
        {
            //StyleTransferm-Fast_1234568_20210402/192168001007-1234568-content.jpg:faststyle1_192168001007
            auto& files = req.get_upload_files();
            std::string filename1 = files[0].get_file_path().substr(middlewaredirpath.size());
            return filename1 + ":" + req.get_multipart_value_by_key1("stylename");
        };
        res.set_delay(true);
        // res.set_status_and_content(cinatra::status_type::ok, "multipart finished");

        std::string modelname = req.get_multipart_value_by_key1("modelname");
        std::string alpha = req.get_multipart_value_by_key1("alpha");
        std::string message = fun(req, alpha, this->__middlewaredirpath);
        message = modelname + "_" + req.get_uuid() + "_" + message + "_" + this->__topic;
        auto con = req.get_conn<cinatra::http_server::type>();
        RWSeparate<cinatra::http_server::type>::inst().Add2Map(con, req.get_uuid());
        SimpleWrapKafka::inst().Add2Kafka(modelname, message);
        
        LOG(INFO) << "request " << req.get_uuid() << " already add kafka:" << message;
    };
    __server.set_http_handler<cinatra::GET, cinatra::POST>("/StyleTransfer/Fast", fun);
}

void HttpServer::__URL_TextToSpeech_Fixed()
{
    auto fun = [this](cinatra::request& req, cinatra::response& res) 
    {
        if(req.get_uuid().empty())
            req.set_uuid(RWSeparate<cinatra::http_server::type>::inst().GetUUID());
        LOG(INFO) << "request " << req.get_uuid() << " already recved files";
        auto fun = [](cinatra::request& req)
        {
            //TextToSpeech_1234566_have a good day:en:0_192168001007
            return req.get_multipart_value_by_key1("text")+ ":" + 
                    req.get_multipart_value_by_key1("language") + ":" +
                    req.get_multipart_value_by_key1("speakerid");
        };
        res.set_delay(true);
        // res.set_status_and_content(cinatra::status_type::ok, "multipart finished");

        std::string modelname = req.get_multipart_value_by_key1("modelname");
        std::string message = fun(req);
        message = modelname + "_" + req.get_uuid() + "_" + message + "_" + this->__topic;
        auto con = req.get_conn<cinatra::http_server::type>();
        RWSeparate<cinatra::http_server::type>::inst().Add2Map(con, req.get_uuid());
        SimpleWrapKafka::inst().Add2Kafka(modelname, message);
        
        LOG(INFO) << "request " << req.get_uuid() << " already add kafka:" << message;
    };
    __server.set_http_handler<cinatra::GET, cinatra::POST>("/TextToSpeech/Fixed", fun);
}