#ifndef TRIANGLE_MESH_INCLUDED
#define TRIANGLE_MESH_INCLUDED

#include <vector>
#include <algorithm>
#include <fstream>
#include <string>
#include <cctype>

#include "TypeDef.hpp"
#include "BoundBox.hpp"
#include "BoundSphere.hpp"
#include "Triangle.hpp"
#include "UnvTrigMeshFile.hpp"
#include "ObjTrigMeshFile.hpp"

// Forward-declared mesh-holder from ObjTrigMeshFile.hpp
// template<class T> struct TriMesh { std::vector<T> vertices; std::vector<uint32_t> indices; };

template< class T >
class TriangleMesh
{
public:
    U32                         trigCount_;
    std::vector< Triangle< T > > trigArray_;
    BoundSphere< T >            boundSphere_;
    BoundBox< T >               boundBox_;

public:
    TriangleMesh()
        : trigCount_(0)
    {
    }

    explicit TriangleMesh(const U32 reservedTrigCount)
        : trigCount_(0)
    {
        trigArray_.reserve(reservedTrigCount);
    }

    void Reset(const U32 reservedTrigCount)
    {
        trigCount_ = 0;
        trigArray_.clear();
        trigArray_.reserve(reservedTrigCount);
        boundSphere_ = BoundSphere< T >();
        boundBox_ = BoundBox< T >();
    }

    void CalculateBounds()
    {
        if (trigArray_.empty()) return;
        boundBox_ = trigArray_[0].GetBoundBox();
        for (const auto& t : trigArray_)
            boundBox_ = boundBox_.UnionWith(t.GetBoundBox());

        boundSphere_.center_ = (boundBox_.min_ + boundBox_.max_) * T(0.5);
        boundSphere_.radius_ = LUV::Length(boundBox_.max_ - boundSphere_.center_);
    }

    void InsertTrig(const Triangle< T >& trig)
    {
        trigArray_.push_back(trig);
        trigCount_ = static_cast<U32>(trigArray_.size());
    }

    /// Generic import: dispatch by file extension (.unv or .obj)
    bool ImportFromFile(const std::string& filePath)
    {
        // extract lowercase extension (without dot)
        auto pos = filePath.find_last_of('.');
        if (pos == std::string::npos) return false;
        std::string ext = filePath.substr(pos + 1);
        std::transform(ext.begin(), ext.end(), ext.begin(), ::tolower);

        // temporary mesh data holder
        TriMesh<T> meshData;
        bool loaded = false;

        if (ext == "unv") {
            UnvTrigMeshFile<T> reader;
            if (!reader.Load(filePath)) return false;
            // copy raw arrays into meshData
            meshData.vertices.assign(
                reader.vertexData_.get(),
                reader.vertexData_.get() + 3 * reader.vertexCount_);
            meshData.indices.assign(
                reader.trigVertexIndex_.get(),
                reader.trigVertexIndex_.get() + 3 * reader.trigCount_);
            loaded = true;
        }
        else if (ext == "obj") {
            ObjTrigMeshFile<T> reader;
            loaded = reader.load(filePath, meshData);
        }
        if (!loaded) return false;

        // rebuild triangle list
        const U32 numTrigs = static_cast<U32>(meshData.indices.size() / 3);
        Reset(numTrigs);
        for (U32 ti = 0; ti < numTrigs; ++ti) {
            U32 i0 = meshData.indices[3 * ti + 0] * 3;
            U32 i1 = meshData.indices[3 * ti + 1] * 3;
            U32 i2 = meshData.indices[3 * ti + 2] * 3;

            LUV::Vec3<T> v0(
                meshData.vertices[i0 + 0],
                meshData.vertices[i0 + 1],
                meshData.vertices[i0 + 2]);
            LUV::Vec3<T> v1(
                meshData.vertices[i1 + 0],
                meshData.vertices[i1 + 1],
                meshData.vertices[i1 + 2]);
            LUV::Vec3<T> v2(
                meshData.vertices[i2 + 0],
                meshData.vertices[i2 + 1],
                meshData.vertices[i2 + 2]);

            trigArray_.emplace_back(v0, v1, v2);
        }
        trigCount_ = numTrigs;
        CalculateBounds();
        return true;
    }
};

#endif // TRIANGLE_MESH_INCLUDED
