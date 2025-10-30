file(GLOB sub_cmake_modules "${CMAKE_CURRENT_LIST_DIR}/*/micropython.cmake")
foreach(cmake_file ${sub_cmake_modules})
    include(${cmake_file})
endforeach()