cmake_minimum_required(VERSION 3.8)
project(BorayAI_M)
set(CMAKE_CXX_STANDARD 17)

set(SOURCE main.cpp httpserver.cpp)

add_definitions(-DASIO_STANDALONE)

set(THIRD_PARTY_PATH ${PROJECT_SOURCE_DIR}/3rdparty)
#file(COPY ${THIRD_PARTY_PATH}/include/ DESTINATION ./include)
include_directories(${THIRD_PARTY_PATH}/include)
include_directories(${PROJECT_SOURCE_DIR}/kafka)
include_directories(${PROJECT_SOURCE_DIR}/net/include)
include_directories(${PROJECT_SOURCE_DIR}/tools)


file(COPY ${THIRD_PARTY_PATH}/lib/rdkafka/ DESTINATION ./lib FOLLOW_SYMLINK_CHAIN)
file(COPY ${THIRD_PARTY_PATH}/lib/json/ DESTINATION ./lib FOLLOW_SYMLINK_CHAIN)
file(COPY ${THIRD_PARTY_PATH}/lib/glog/ DESTINATION ./lib FOLLOW_SYMLINK_CHAIN)
file(COPY ${THIRD_PARTY_PATH}/lib/other/ DESTINATION ./lib FOLLOW_SYMLINK_CHAIN)

message(string(${CMAKE_CURRENT_SOURCE_DIR}))
link_directories(./build/lib)
#link_directories(${THIRD_PARTY_PATH}/lib)
#link_directories(${THIRD_PARTY_PATH}/lib/rdkafka)
#link_directories(${THIRD_PARTY_PATH}/lib/json)



ADD_SUBDIRECTORY(kafka)
#ADD_SUBDIRECTORY(net)
ADD_SUBDIRECTORY(queue)

add_executable(${PROJECT_NAME} ${SOURCE})
# target_compile_features(${PROJECT_NAME} PRIVATE cxx_std_17)
# target_link_libraries(${PROJECT_NAME} glog pthread uokafka)
target_link_libraries(${PROJECT_NAME} uoqueue pthread uokafka rdkafka++ uuid jsoncpp glog)
