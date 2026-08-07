#include <vector>
#include <cmath>

namespace Polyglot3DEngine {
    class PhysicsCore {
    public:
        PhysicsCore() {}
        ~PhysicsCore() {}

        struct Vector3 {
            float x, y, z;
        };

        Vector3 applyGravity(Vector3 velocity, float dt) {
            velocity.y -= 9.8f * dt;
            return velocity;
        }

        Vector3 updatePosition(Vector3 position, Vector3 velocity, float dt) {
            position.x += velocity.x * dt;
            position.y += velocity.y * dt;
            position.z += velocity.z * dt;
            return position;
        }

        float calculateDistance(Vector3 a, Vector3 b) {
            return std::sqrt(std::pow(b.x - a.x, 2) + std::pow(b.y - a.y, 2) + std::pow(b.z - a.z, 2));
        }
    };
} // namespace Polyglot3DEngine
