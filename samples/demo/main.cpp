#include <array>
#include <cctype>
#include <cstdint>
#include <iostream>
#include <string>
#include <string_view>

#if defined(_MSC_VER)
#define NOINLINE __declspec(noinline)
#else
#define NOINLINE __attribute__((noinline))
#endif

namespace {

constexpr std::uint32_t kAccessMask = 0xa5c3f17dU;
constexpr std::uint32_t kCodeRange = 900000U;
constexpr std::uint32_t kCodeFloor = 100000U;

NOINLINE std::uint32_t rotate_left(std::uint32_t value, unsigned int count) {
    return (value << count) | (value >> (32U - count));
}

NOINLINE std::uint32_t hash_name(std::string_view name) {
    std::uint32_t state = 2166136261U;
    for (unsigned char ch : name) {
        const auto normalized = static_cast<unsigned char>(std::tolower(ch));
        state ^= normalized;
        state *= 16777619U;
        state = rotate_left(state, 5U) ^ 0x9e3779b9U;
    }
    return state;
}

NOINLINE std::uint32_t compute_access_code(std::string_view name) {
    return ((hash_name(name) ^ kAccessMask) % kCodeRange) + kCodeFloor;
}

NOINLINE bool parse_six_digits(std::string_view text, std::uint32_t& value) {
    if (text.size() != 6U) {
        return false;
    }

    std::uint32_t parsed = 0;
    for (char ch : text) {
        if (ch < '0' || ch > '9') {
            return false;
        }
        parsed = (parsed * 10U) + static_cast<std::uint32_t>(ch - '0');
    }

    value = parsed;
    return true;
}

NOINLINE bool validate_access_code(std::string_view name, std::string_view code) {
    std::uint32_t supplied = 0;
    if (name.size() < 3U || !parse_six_digits(code, supplied)) {
        return false;
    }

    const std::uint32_t expected = compute_access_code(name);
    std::uint32_t difference = supplied ^ expected;
    difference |= difference >> 16U;
    difference |= difference >> 8U;
    difference |= difference >> 4U;
    difference |= difference >> 2U;
    difference |= difference >> 1U;
    return (difference & 1U) == 0U;
}

NOINLINE std::string decode_banner() {
    constexpr std::array<std::uint8_t, 18> encoded = {
        0x1a, 0x26, 0x08, 0x0b, 0x47, 0x2b, 0x03, 0x11, 0x1f,
        0x0f, 0x0a, 0x08, 0x5f, 0xc6, 0xe0, 0xe5, 0xe4, 0xaf,
    };

    std::string decoded;
    decoded.reserve(encoded.size());
    std::uint8_t key = 0x5bU;
    for (std::uint8_t byte : encoded) {
        decoded.push_back(static_cast<char>(byte ^ key));
        key = static_cast<std::uint8_t>(key + 3U);
    }
    return decoded;
}

NOINLINE int calculate_signal_score(const std::array<int, 8>& samples) {
    int score = 0;
    int previous = samples.front();

    for (int sample : samples) {
        const int delta = sample - previous;
        if (sample > 75) {
            score += 4;
        } else if (sample < 20) {
            score -= 2;
        } else {
            score += 1;
        }

        if (delta > 30 || delta < -30) {
            score += 3;
        }
        previous = sample;
    }

    return score;
}

NOINLINE const char* classify_signal(int score) {
    if (score >= 20) {
        return "critical";
    }
    if (score >= 10) {
        return "suspicious";
    }
    if (score >= 0) {
        return "normal";
    }
    return "quiet";
}

int run_demo() {
    const std::string name = "analyst";
    const std::string valid_code = std::to_string(compute_access_code(name));
    const std::array<int, 8> samples = {12, 18, 82, 79, 15, 91, 45, 88};
    const int score = calculate_signal_score(samples);

    std::cout << decode_banner() << '\n';
    std::cout << "user: " << name << '\n';
    std::cout << "access: "
              << (validate_access_code(name, valid_code) ? "granted" : "denied")
              << '\n';
    std::cout << "signal: " << classify_signal(score) << " (" << score << ")\n";
    return 0;
}

}  // namespace

int main(int argc, char** argv) {
    if (argc == 2 && std::string_view(argv[1]) == "--demo") {
        return run_demo();
    }

    std::string name;
    std::string code;

    std::cout << "Name: ";
    std::getline(std::cin, name);
    std::cout << "Six-digit access code: ";
    std::getline(std::cin, code);

    if (!validate_access_code(name, code)) {
        std::cout << "Access denied.\n";
        return 1;
    }

    std::cout << decode_banner() << '\n';
    std::cout << "Access granted.\n";
    return 0;
}
