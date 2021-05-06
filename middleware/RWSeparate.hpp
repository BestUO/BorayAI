#pragma once

#include <iostream>
#include <map>
#include <chrono>
#include <thread>
#include <uuid.h>
#include "singleton.hpp"
#include "simplewrapkafka.h"
// #include "net/include/cinatra.hpp"
// #include "net/include/cinatra/response_cv.hpp"
// #include <cinatra.hpp>
// #include <define.h>
// #include <response_cv.hpp>

// template <typename T> class connection;
// using ttt_type = std::weak_ptr<cinatra::connection<cinatra::NonSSL>>;

template <typename T>
class RWSeparate:public Singleton<RWSeparate<T>>
{
public:
    std::string GetUUID()
    {
        uuid_t myuuid;
        uuid_generate(myuuid);
        char chuuid[36] = {0};
        uuid_unparse(myuuid,chuuid);
        std::string str(chuuid);
        str.erase(remove(str.begin(),str.end(),'-'),str.end());
        return str;
    }

    bool Add2Map(std::shared_ptr<cinatra::connection<T>> con, std::string uuid)
    {
        std::unique_lock<std::mutex> lck(_mutex);
        auto res = _mapcon.insert({uuid, con});
        return res.second;
    }

    bool ResponseClient(std::string resultdirpath, std::string message)
    {
        //"/home/uncle_orange/mydevice/BorayAI/data/backend/"
        //"e9dd99a3517f4312947feada2d982d00_20210404/192168001007-e9dd99a3517f4312947feada2d982d00-result.jpg"
        LOG(INFO) << "recv message from kafka:" << message;
        std::unique_lock<std::mutex> lck(_mutex);
        std::string uuid(message.substr(0,32));
        auto iter = _mapcon.find(uuid);
        if(iter != _mapcon.end())
        {
            std::string filename = resultdirpath + message.substr(33);
            auto file = std::make_shared<std::ifstream>(std::move(filename), std::ios::binary);

            std::string content;
            const size_t size = 5 * 1024 * 1024;
            content.resize(size);
            file->read(&content[0], size);
            int64_t read_len = (int64_t)file->gcount();

            if (read_len < size)
                content.resize(read_len);

            iter->second->get_res().set_status_and_content(cinatra::status_type::ok, std::move(content),cinatra::req_content_type::multipart);

            // iter->second->get_res().set_status_and_content(cinatra::status_type::ok, "OK");

            iter->second->response_now();
            _mapcon.erase(iter);
            return true;
        }
        return false;
    }
private:
    // int _max_thread_num = std::thread::hardware_concurrency();
    std::mutex _mutex;
    // RTE_Ring _ret_ring{"Myring",1024,false};
    std::map<std::string, std::shared_ptr<cinatra::connection<T>>> _mapcon;
};