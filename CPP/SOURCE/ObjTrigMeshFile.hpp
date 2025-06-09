#ifndef OBJ_TRIG_MESH_FILE_INCLUDED
#define OBJ_TRIG_MESH_FILE_INCLUDED

#include <array>
#include <fstream>
#include <string>
#include <sstream>
#include <vector>
#include <cstdint>
#include "TypeDef.hpp"

// Simple triangle-mesh holder
template<typename T>
struct TriMesh {
    std::vector<T>        vertices;       // flat list: x0,y0,z0, x1,y1,z1, ...
    std::vector<uint32_t> indices;        // triplets of vertex indices (0-based)
};

// Reader interface
template<typename T>
class IMeshFileReader {
public:
    virtual ~IMeshFileReader() = default;
    virtual bool load(const std::string& path, TriMesh<T>& out) = 0;
};

// OBJ reader implementation
template<typename T>
class ObjTrigMeshFile : public IMeshFileReader<T> {
public: 
    bool load(const std::string& path, TriMesh<T>& out) override {
        std::cout << "trying to load obj" << std::endl;
        std::ifstream in(path);
        if (!in.is_open()) return false;

        std::vector<std::array<T, 3>> tempVerts;
        std::string line;

        while (std::getline(in, line)) {
            if (line.empty() || line[0] == '#') continue;
            std::istringstream ss(line);
            std::string tag;
            ss >> tag;

            if (tag == "v") {
                T x, y, z;
                ss >> x >> y >> z;
                tempVerts.push_back(std::array<T, 3>{x, y, z});
            }
            else if (tag == "f") {
                // only support triangle faces: f i1 i2 i3 (with optional slash formats)
                auto parseIndex = [&](const std::string& token) {
                    std::istringstream ts(token);
                    uint32_t vi;
                    ts >> vi;
                    return vi - 1; // OBJ is 1-based
                    };

                std::string v1, v2, v3;
                ss >> v1 >> v2 >> v3;
                out.indices.push_back(parseIndex(v1));
                out.indices.push_back(parseIndex(v2));
                out.indices.push_back(parseIndex(v3));
            }
            // ignore vt, vn, other tags
        }

        // flatten vertices
        out.vertices.reserve(tempVerts.size() * 3);
        for (const auto& v : tempVerts) {
            out.vertices.push_back(v[0]);
            out.vertices.push_back(v[1]);
            out.vertices.push_back(v[2]);
        }

        return true;
    }
};

#endif // OBJ_TRIG_MESH_FILE_INCLUDED
