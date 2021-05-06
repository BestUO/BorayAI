#include <iostream>
#include "queue/rte_ring.h"
#include <tuple>
#include <vector>
#include <chrono>
#include <thread>
#include <cinatra.hpp>
#include <glog/logging.h>
#include <simplewrapkafka.h>
#include <json/json.h>
#include "RWSeparate.hpp"
#include <fstream>
#include <filesystem>
#include "httpserver.h"


using namespace cinatra;

std::tuple<int,double,std::string> f() {
    return std::make_tuple(1,2.3,"456");
}

void testmutex()
{
    MutexQueueWrap<void*> aa(1024);
    std::vector<void*> v1;
    for(int n = 0;n < 5000000;n++)
        v1.push_back(new int(10000000 - n));

    std::vector<std::thread> vp;
    for(int a = 0;a<2;a++)
    {
        std::thread t([&]()
        {
            for (auto a:v1)
                while(!aa.Push(a))
                {
                    // std::cout << "aaaaa";
                    std::this_thread::sleep_for(std::chrono::milliseconds(1));
                }

        });
        vp.emplace_back(std::move(t));
    }


    std::vector<std::thread> vc;
    for(int a = 0;a<4;a++)
    {
        std::thread t([&]()
        {
            int total = 0;
            while(true)
            {
                void *ptr = aa.GetAndPop();
                if(ptr)
                    total += *(int*)ptr;
            }
        });
        vc.emplace_back(std::move(t));
    }

    auto startTime = std::chrono::high_resolution_clock::now();
    for(auto t = vp.begin();t!=vp.end();t++)
        t->join();
    // p2.join();
    auto endTime = std::chrono::high_resolution_clock::now();
    std::chrono::duration<double, std::milli> fp_ms = endTime - startTime;
    std::cout << "3 " << fp_ms.count() << std::endl;
    
    for(auto t = vc.begin();t!=vc.end();t++)
        t->join();

    for(auto a:v1)
        delete (int*)a;
}


void testfreelock()
{
    auto aaa = RTE_Ring("Myring",1024,false);

    std::vector<void*> v1,v2;
    for(int n = 0;n < 5000000;n++)
        v1.push_back(new int(n));

    std::vector<std::thread> vp;
    for(int a = 0;a<2;a++)
    {
        std::thread t([&]()
        {
            for (auto a:v1)
                while(!aaa.rte_ring_mp_enqueue_bulk(&a, 1, nullptr))
                    std::this_thread::sleep_for(std::chrono::milliseconds(1));
        });
        vp.emplace_back(std::move(t));
    }

    std::vector<std::thread> vc;
    for(int a = 0;a<4;a++)
    {
        std::thread t([&]()
        {
            int total = 0;
            while(true)
            {
                void *ptr = nullptr;
                int num = aaa.rte_ring_mc_dequeue_bulk(&ptr, 1, nullptr);
                if(num)
                    total += *(int*)ptr;
            }
            
        });
        vc.emplace_back(std::move(t));
    }

    auto startTime = std::chrono::high_resolution_clock::now();
    for(auto t = vp.begin();t!=vp.end();t++)
        t->join();
    auto endTime = std::chrono::high_resolution_clock::now();
    std::chrono::duration<double, std::milli> fp_ms = endTime - startTime;
    std::cout << "3 " << fp_ms.count() << std::endl;

    for(auto t = vc.begin();t!=vc.end();t++)
        t->join();
    for(auto a:v1)
        delete (int*)a;
}

int ttt()
{
    int max_thread_num = std::thread::hardware_concurrency();
    http_server server(max_thread_num);
    server.listen("0.0.0.0", "7086");
    server.set_http_handler<GET, POST>("/", [&](request& req, response& res) 
    {
        res.set_status_and_content(status_type::ok, "multipart finished");
    });
    server.enable_timeout(false);
    server.run();
    return 0;
}

std::tuple<std::string, std::string, std::string, std::string, std::string, std::string,std::string> readStrJson() 
{
	Json::Reader reader;
	Json::Value root;
 
	std::ifstream in("../config.json", std::ios::binary);
	if( !in.is_open() || !reader.parse(in,root))
	{ 
        std::cout << "Error read config.json\n"; 
        return std::tuple<std::string, std::string, std::string, std::string, std::string, std::string,std::string>("","","","","","","");
	}

    auto fun = [](Json::Value &v) -> std::string
    {
        std::string list2str = v[0].asString();
        for(auto n = 1; n < v.size(); n++)
            list2str += "," + v[n].asString();
        return list2str;
    };
 
    auto MiddlewareTopic = root["MiddlewareTopic"];
    std::string topic = fun(MiddlewareTopic);
    auto bootstrapservers = root["bootstrap.servers"];
    std::string brokers = fun(bootstrapservers);
    auto GroupID = root["GroupID"].asString();
    auto MiddlewareDirPath = root["MiddlewareDirPath"].asString();
    auto ResultDirPath = root["ResultDirPath"].asString();
    auto Port = root["Port"].asString();
    auto MiddlewareLogPath = root["middlewarelogpath"].asString();

	in.close();
    return std::tuple<std::string, std::string, std::string, std::string, std::string, std::string, std::string>
        (topic,brokers,GroupID,MiddlewareDirPath,ResultDirPath, Port, MiddlewareLogPath);
}

int main()
{
    auto [topic,brokers,groupid,middlewaredirpath,resultdirpath,port,middlewarelogpath] = readStrJson();
    if(topic.empty() || brokers.empty() || groupid.empty() || middlewaredirpath.empty() || resultdirpath.empty() || port.empty()|| middlewarelogpath.empty())
    {
        std::cout << "json error" << std::endl;
        return 0;
    }
    std::filesystem::create_directories(middlewarelogpath);

    FLAGS_log_dir = middlewarelogpath;
    FLAGS_max_log_size=1024;
    FLAGS_stop_logging_if_full_disk=true;
    FLAGS_logbufsecs=5;
    google::InitGoogleLogging("BorayAI_Middleware.log");
    LOG(INFO) << "start middleware";

    // ttt();
    
    SimpleWrapKafka::inst().CreateProducer(brokers);
    SimpleWrapKafka::inst().CreateConsumer(brokers,topic,groupid,[resultdirpath](std::string message)
    {
        RWSeparate<http_server::type>::inst().ResponseClient(resultdirpath, message);
    });

    HttpServer httpserver("0.0.0.0", port, topic , middlewaredirpath, 1);
    httpserver.Run();

    // SimpleWrapKafka::inst().Add2Kafka(Topic,"wrap2");
    // RWSeparate::inst().printt();
    
    // net();
}