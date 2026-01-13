#pragma once

#include <pybind11/pybind11.h>
#include <pybind11/stl.h>
#include <pybind11/numpy.h>
#include <string>
#include <vector>

// Include EDSDK headers
#include "../../EDSDK/Header/EDSDK.h"
#include "../../EDSDK/Header/EDSDKTypes.h"
#include "../../EDSDK/Header/EDSDKErrors.h"

namespace py = pybind11;

class EDSDKWrapper {
public:
    EDSDKWrapper();
    ~EDSDKWrapper();
    
    // Initialization and cleanup
    bool initialize();
    bool terminate();
    bool is_initialized() const;
    
    // Camera management
    std::vector<std::string> get_camera_list();
    bool connect_camera(int camera_index);
    bool disconnect_camera();
    bool is_camera_connected() const;
    
    // Camera information
    std::string get_camera_name() const;
    std::string get_camera_firmware_version() const;
    
    // Live view
    bool start_live_view();
    bool stop_live_view();
    bool is_live_view_active() const;
    py::array_t<uint8_t> get_live_view_image();
    
    // Capture
    bool capture_photo(const std::string& filename);
    bool auto_focus();
    bool auto_expose();
    
    // Properties
    bool set_property(int property_id, int value);
    int get_property(int property_id);
    
    // Error handling
    std::string get_last_error() const;
    int get_last_error_code() const;

private:
    bool m_initialized;
    bool m_camera_connected;
    bool m_live_view_active;
    EdsCameraRef m_camera;
    EdsError m_last_error;
    
    // Helper functions
    void set_last_error(EdsError error);
    std::string error_to_string(EdsError error) const;
    
    // Live view helpers
    EdsStreamRef create_memory_stream(size_t size);
    bool download_live_view_image(EdsStreamRef stream);
};

// Utility functions for EDSDK types
std::string eds_error_to_string(EdsError error);
std::string eds_property_id_to_string(EdsPropertyID property_id);