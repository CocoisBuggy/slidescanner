#include "edsdk_wrapper.h"
#include <iostream>
#include <memory>
#include <cstring>

// Pybind11 bindings
PYBIND11_MODULE(edsdk, m) {
    m.doc() = "Python bindings for Canon EDSDK";
    
    py::class_<EDSDKWrapper>(m, "EDSDK")
        .def(py::init<>())
        .def("initialize", &EDSDKWrapper::initialize)
        .def("terminate", &EDSDKWrapper::terminate)
        .def("is_initialized", &EDSDKWrapper::is_initialized)
        .def("get_camera_list", &EDSDKWrapper::get_camera_list)
        .def("connect_camera", &EDSDKWrapper::connect_camera)
        .def("disconnect_camera", &EDSDKWrapper::disconnect_camera)
        .def("is_camera_connected", &EDSDKWrapper::is_camera_connected)
        .def("get_camera_name", &EDSDKWrapper::get_camera_name)
        .def("get_camera_firmware_version", &EDSDKWrapper::get_camera_firmware_version)
        .def("start_live_view", &EDSDKWrapper::start_live_view)
        .def("stop_live_view", &EDSDKWrapper::stop_live_view)
        .def("is_live_view_active", &EDSDKWrapper::is_live_view_active)
        .def("get_live_view_image", &EDSDKWrapper::get_live_view_image)
        .def("capture_photo", &EDSDKWrapper::capture_photo)
        .def("auto_focus", &EDSDKWrapper::auto_focus)
        .def("auto_expose", &EDSDKWrapper::auto_expose)
        .def("set_property", &EDSDKWrapper::set_property)
        .def("get_property", &EDSDKWrapper::get_property)
        .def("get_last_error", &EDSDKWrapper::get_last_error)
        .def("get_last_error_code", &EDSDKWrapper::get_last_error_code);
    
    // Utility functions
    m.def("eds_error_to_string", &eds_error_to_string);
    m.def("eds_property_id_to_string", &eds_property_id_to_string);
}

// EDSDKWrapper implementation
EDSDKWrapper::EDSDKWrapper() 
    : m_initialized(false), m_camera_connected(false), 
      m_live_view_active(false), m_camera(nullptr), m_last_error(EDS_ERR_OK) {
}

EDSDKWrapper::~EDSDKWrapper() {
    if (m_camera_connected) {
        disconnect_camera();
    }
    if (m_initialized) {
        terminate();
    }
}

bool EDSDKWrapper::initialize() {
    if (m_initialized) {
        return true;
    }
    
    m_last_error = EdsInitializeSDK();
    if (m_last_error == EDS_ERR_OK) {
        m_initialized = true;
        return true;
    }
    
    return false;
}

bool EDSDKWrapper::terminate() {
    if (!m_initialized) {
        return true;
    }
    
    if (m_camera_connected) {
        disconnect_camera();
    }
    
    m_last_error = EdsTerminateSDK();
    if (m_last_error == EDS_ERR_OK) {
        m_initialized = false;
        return true;
    }
    
    return false;
}

bool EDSDKWrapper::is_initialized() const {
    return m_initialized;
}

std::vector<std::string> EDSDKWrapper::get_camera_list() {
    std::vector<std::string> camera_names;
    
    if (!m_initialized) {
        set_last_error(EDS_ERR_NOT_INITIALIZED);
        return camera_names;
    }
    
    EdsCameraListRef camera_list = nullptr;
    m_last_error = EdsGetCameraList(&camera_list);
    if (m_last_error != EDS_ERR_OK) {
        return camera_names;
    }
    
    EdsUInt32 count = 0;
    m_last_error = EdsGetChildCount(camera_list, &count);
    if (m_last_error != EDS_ERR_OK) {
        EdsRelease(camera_list);
        return camera_names;
    }
    
    for (EdsUInt32 i = 0; i < count; i++) {
        EdsCameraRef camera = nullptr;
        m_last_error = EdsGetChildAtIndex(camera_list, i, &camera);
        if (m_last_error == EDS_ERR_OK) {
            EdsDeviceInfo device_info;
            m_last_error = EdsGetDeviceInfo(camera, &device_info);
            if (m_last_error == EDS_ERR_OK) {
                camera_names.push_back(std::string(device_info.szDeviceDescription));
            }
            EdsRelease(camera);
        }
    }
    
    EdsRelease(camera_list);
    return camera_names;
}

bool EDSDKWrapper::connect_camera(int camera_index) {
    if (!m_initialized) {
        set_last_error(EDS_ERR_NOT_INITIALIZED);
        return false;
    }
    
    if (m_camera_connected) {
        return true;
    }
    
    EdsCameraListRef camera_list = nullptr;
    m_last_error = EdsGetCameraList(&camera_list);
    if (m_last_error != EDS_ERR_OK) {
        return false;
    }
    
    m_last_error = EdsGetChildAtIndex(camera_list, camera_index, &m_camera);
    EdsRelease(camera_list);
    
    if (m_last_error != EDS_ERR_OK) {
        return false;
    }
    
    m_last_error = EdsOpenSession(m_camera);
    if (m_last_error == EDS_ERR_OK) {
        m_camera_connected = true;
        return true;
    }
    
    EdsRelease(m_camera);
    m_camera = nullptr;
    return false;
}

bool EDSDKWrapper::disconnect_camera() {
    if (!m_camera_connected) {
        return true;
    }
    
    if (m_live_view_active) {
        stop_live_view();
    }
    
    m_last_error = EdsCloseSession(m_camera);
    if (m_camera) {
        EdsRelease(m_camera);
        m_camera = nullptr;
    }
    
    if (m_last_error == EDS_ERR_OK) {
        m_camera_connected = false;
        return true;
    }
    
    return false;
}

bool EDSDKWrapper::is_camera_connected() const {
    return m_camera_connected;
}

std::string EDSDKWrapper::get_camera_name() const {
    if (!m_camera_connected || !m_camera) {
        return "";
    }
    
    EdsDeviceInfo device_info;
    m_last_error = EdsGetDeviceInfo(m_camera, &device_info);
    if (m_last_error == EDS_ERR_OK) {
        return std::string(device_info.szDeviceDescription);
    }
    
    return "";
}

std::string EDSDKWrapper::get_camera_firmware_version() const {
    if (!m_camera_connected || !m_camera) {
        return "";
    }
    
    EdsDeviceInfo device_info;
    m_last_error = EdsGetDeviceInfo(m_camera, &device_info);
    if (m_last_error == EDS_ERR_OK) {
        return std::string(device_info.szFirmwareVersion);
    }
    
    return "";
}

// Placeholder implementations for now
bool EDSDKWrapper::start_live_view() {
    set_last_error(EDS_ERR_UNIMPLEMENTED);
    return false;
}

bool EDSDKWrapper::stop_live_view() {
    set_last_error(EDS_ERR_UNIMPLEMENTED);
    return false;
}

bool EDSDKWrapper::is_live_view_active() const {
    return m_live_view_active;
}

py::array_t<uint8_t> EDSDKWrapper::get_live_view_image() {
    set_last_error(EDS_ERR_UNIMPLEMENTED);
    return py::array_t<uint8_t>();
}

bool EDSDKWrapper::capture_photo(const std::string& filename) {
    set_last_error(EDS_ERR_UNIMPLEMENTED);
    return false;
}

bool EDSDKWrapper::auto_focus() {
    set_last_error(EDS_ERR_UNIMPLEMENTED);
    return false;
}

bool EDSDKWrapper::auto_expose() {
    set_last_error(EDS_ERR_UNIMPLEMENTED);
    return false;
}

bool EDSDKWrapper::set_property(int property_id, int value) {
    set_last_error(EDS_ERR_UNIMPLEMENTED);
    return false;
}

int EDSDKWrapper::get_property(int property_id) {
    set_last_error(EDS_ERR_UNIMPLEMENTED);
    return -1;
}

std::string EDSDKWrapper::get_last_error() const {
    return error_to_string(m_last_error);
}

int EDSDKWrapper::get_last_error_code() const {
    return static_cast<int>(m_last_error);
}

void EDSDKWrapper::set_last_error(EdsError error) {
    m_last_error = error;
}

std::string EDSDKWrapper::error_to_string(EdsError error) const {
    return eds_error_to_string(error);
}

// Utility function implementations
std::string eds_error_to_string(EdsError error) {
    switch (error) {
        case EDS_ERR_OK: return "EDS_ERR_OK";
        case EDS_ERR_UNIMPLEMENTED: return "EDS_ERR_UNIMPLEMENTED";
        case EDS_ERR_NOT_INITIALIZED: return "EDS_ERR_NOT_INITIALIZED";
        default: return "Unknown EDSDK Error";
    }
}

std::string eds_property_id_to_string(EdsPropertyID property_id) {
    switch (property_id) {
        default: return "Unknown Property";
    }
}