#include "atlasmirror_sdk_impl.h"
#include <sstream>
#include <fstream>
#include <iostream>
#include <iomanip>
#include <cstdio>
#include <memory>
#include <array>
#include <cstring>
#include <cstdint>
#include <sys/stat.h>

// --- Lightweight Self-Contained MD5 Implementation ---
namespace {

struct MD5Context {
    uint32_t state[4];
    uint32_t count[2];
    uint8_t buffer[64];
};

#define S11 7
#define S12 12
#define S13 17
#define S14 22
#define S21 5
#define S22 9
#define S23 14
#define S24 20
#define S31 4
#define S32 11
#define S33 16
#define S34 23
#define S41 6
#define S42 10
#define S43 15
#define S44 21

#define F(x, y, z) (((x) & (y)) | ((~x) & (z)))
#define G(x, y, z) (((x) & (z)) | ((y) & (~z)))
#define H(x, y, z) ((x) ^ (y) ^ (z))
#define I(x, y, z) ((y) ^ ((x) | (~z)))

#define ROTATE_LEFT(x, n) (((x) << (n)) | ((x) >> (32-(n))))

#define FF(a, b, c, d, x, s, ac) { \
 (a) += F ((b), (c), (d)) + (x) + (uint32_t)(ac); \
 (a) = ROTATE_LEFT ((a), (s)); \
 (a) += (b); \
  }
#define GG(a, b, c, d, x, s, ac) { \
 (a) += G ((b), (c), (d)) + (x) + (uint32_t)(ac); \
 (a) = ROTATE_LEFT ((a), (s)); \
 (a) += (b); \
  }
#define HH(a, b, c, d, x, s, ac) { \
 (a) += H ((b), (c), (d)) + (x) + (uint32_t)(ac); \
 (a) = ROTATE_LEFT ((a), (s)); \
 (a) += (b); \
  }
#define II(a, b, c, d, x, s, ac) { \
 (a) += I ((b), (c), (d)) + (x) + (uint32_t)(ac); \
 (a) = ROTATE_LEFT ((a), (s)); \
 (a) += (b); \
  }

static void MD5Transform(uint32_t state[4], const uint8_t block[64]) {
    uint32_t a = state[0], b = state[1], c = state[2], d = state[3], x[16];
    for (int i = 0, j = 0; j < 64; i++, j += 4)
        x[i] = ((uint32_t)block[j]) | (((uint32_t)block[j+1]) << 8) |
               (((uint32_t)block[j+2]) << 16) | (((uint32_t)block[j+3]) << 24);

    FF (a, b, c, d, x[ 0], S11, 0xd76aa478);
    FF (d, a, b, c, x[ 1], S12, 0xe8c7b756);
    FF (c, d, a, b, x[ 2], S13, 0x242070db);
    FF (b, c, d, a, x[ 3], S14, 0xc1bdceee);
    FF (a, b, c, d, x[ 4], S11, 0xf57c0faf);
    FF (d, a, b, c, x[ 5], S12, 0x4787c62a);
    FF (c, d, a, b, x[ 6], S13, 0xa8304613);
    FF (b, c, d, a, x[ 7], S14, 0xfd469501);
    FF (a, b, c, d, x[ 8], S11, 0x698098d8);
    FF (d, a, b, c, x[ 9], S12, 0x8b44f7af);
    FF (c, d, a, b, x[10], S13, 0xffff5bb1);
    FF (b, c, d, a, x[11], S14, 0x895cd7be);
    FF (a, b, c, d, x[12], S11, 0x6b901122);
    FF (d, a, b, c, x[13], S12, 0xfd987193);
    FF (c, d, a, b, x[14], S13, 0xa679438e);
    FF (b, c, d, a, x[15], S14, 0x49b40821);

    GG (a, b, c, d, x[ 1], S21, 0xf61e2562);
    GG (d, a, b, c, x[ 6], S22, 0xc040b340);
    GG (c, d, a, b, x[11], S23, 0x265e5a51);
    GG (b, c, d, a, x[ 0], S24, 0xe9b6c7aa);
    GG (a, b, c, d, x[ 5], S21, 0xd62f105d);
    GG (d, a, b, c, x[10], S22,  0x2441453);
    GG (c, d, a, b, x[15], S23, 0xd8a1e681);
    GG (b, c, d, a, x[ 4], S24, 0xe7d3fbc8);
    GG (a, b, c, d, x[ 9], S21, 0x21e1cde6);
    GG (d, a, b, c, x[14], S22, 0xc33707d6);
    GG (c, d, a, b, x[ 3], S23, 0xf4d50d87);
    GG (b, c, d, a, x[ 8], S24, 0x455a14ed);
    GG (a, b, c, d, x[13], S21, 0xa9e3e905);
    GG (d, a, b, c, x[ 2], S22, 0xfcefa3f8);
    GG (c, d, a, b, x[ 7], S23, 0x676f02d9);
    GG (b, c, d, a, x[12], S24, 0x8d2a4c8a);

    HH (a, b, c, d, x[ 5], S31, 0xfffa3942);
    HH (d, a, b, c, x[ 8], S32, 0x8771f681);
    HH (c, d, a, b, x[11], S33, 0x6d9d6122);
    HH (b, c, d, a, x[14], S34, 0xfde5380c);
    HH (a, b, c, d, x[ 1], S31, 0xa4beea44);
    HH (d, a, b, c, x[ 4], S32, 0x4bdecfa9);
    HH (c, d, a, b, x[ 7], S33, 0xf6bb4b60);
    HH (b, c, d, a, x[10], S34, 0xbebfbc70);
    HH (a, b, c, d, x[13], S31, 0x289b7ec6);
    HH (d, a, b, c, x[ 0], S32, 0xeaa127fa);
    HH (c, d, a, b, x[ 3], S33, 0xd4ef3085);
    HH (b, c, d, a, x[ 6], S34,  0x4881d05);
    HH (a, b, c, d, x[ 9], S31, 0xd9d4d039);
    HH (d, a, b, c, x[12], S32, 0xe6db99e5);
    HH (c, d, a, b, x[15], S33, 0x1fa27cf8);
    HH (b, c, d, a, x[ 2], S34, 0xc4ac5665);

    II (a, b, c, d, x[ 0], S41, 0xf4292244);
    II (d, a, b, c, x[ 7], S42, 0x432aff97);
    II (c, d, a, b, x[14], S43, 0xab9423a7);
    II (b, c, d, a, x[ 5], S44, 0xfc93a039);
    II (a, b, c, d, x[12], S41, 0x655b59c3);
    II (d, a, b, c, x[ 3], S42, 0x8f0ccc92);
    II (c, d, a, b, x[10], S43, 0xffeff47d);
    II (b, c, d, a, x[ 1], S44, 0x85845dd1);
    II (a, b, c, d, x[ 8], S41, 0x6fa87e4f);
    II (d, a, b, c, x[15], S42, 0xfe2ce6e0);
    II (c, d, a, b, x[ 6], S43, 0xa3014314);
    II (b, c, d, a, x[13], S44, 0x4e0811a1);
    II (a, b, c, d, x[ 4], S41, 0xf7537e82);
    II (d, a, b, c, x[11], S42, 0xbd3af235);
    II (c, d, a, b, x[ 2], S43, 0x2ad7d2bb);
    II (b, c, d, a, x[ 9], S44, 0xeb86d391);

    state[0] += a;
    state[1] += b;
    state[2] += c;
    state[3] += d;
}

static void MD5Init(MD5Context *context) {
    context->count[0] = context->count[1] = 0;
    context->state[0] = 0x67452301;
    context->state[1] = 0xefcdab89;
    context->state[2] = 0x98badcfe;
    context->state[3] = 0x10325476;
}

static void MD5Update(MD5Context *context, const uint8_t *input, size_t inputLen) {
    size_t i = 0, index = (context->count[0] >> 3) & 0x3F;
    if ((context->count[0] += ((uint32_t)inputLen << 3)) < ((uint32_t)inputLen << 3))
        context->count[1]++;
    context->count[1] += ((uint32_t)inputLen >> 29);
    size_t partLen = 64 - index;

    if (inputLen >= partLen) {
        std::memcpy(&context->buffer[index], input, partLen);
        MD5Transform(context->state, context->buffer);
        for (i = partLen; i + 63 < inputLen; i += 64)
            MD5Transform(context->state, &input[i]);
        index = 0;
    }
    std::memcpy(&context->buffer[index], &input[i], inputLen - i);
}

static void MD5Final(uint8_t digest[16], MD5Context *context) {
    static const uint8_t PADDING[64] = {
        0x80, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
        0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
        0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
        0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0
    };
    uint8_t bits[8];
    for (int i = 0, j = 0; j < 8; i++, j += 4) {
        bits[j] = (uint8_t)(context->count[i] & 0xFF);
        bits[j+1] = (uint8_t)((context->count[i] >> 8) & 0xFF);
        bits[j+2] = (uint8_t)((context->count[i] >> 16) & 0xFF);
        bits[j+3] = (uint8_t)((context->count[i] >> 24) & 0xFF);
    }
    size_t index = (context->count[0] >> 3) & 0x3F;
    size_t padLen = (index < 56) ? (56 - index) : (120 - index);
    MD5Update(context, PADDING, padLen);
    MD5Update(context, bits, 8);
    for (int i = 0, j = 0; j < 16; i++, j += 4) {
        digest[j] = (uint8_t)(context->state[i] & 0xFF);
        digest[j+1] = (uint8_t)((context->state[i] >> 8) & 0xFF);
        digest[j+2] = (uint8_t)((context->state[i] >> 16) & 0xFF);
        digest[j+3] = (uint8_t)((context->state[i] >> 24) & 0xFF);
    }
}

static std::string computeFileMd5(const std::string &filepath) {
    std::ifstream file(filepath, std::ios::binary);
    if (!file) return "";
    MD5Context ctx;
    MD5Init(&ctx);
    char buffer[65536];
    while (file.read(buffer, sizeof(buffer))) {
        MD5Update(&ctx, reinterpret_cast<const uint8_t*>(buffer), file.gcount());
    }
    if (file.gcount() > 0) {
        MD5Update(&ctx, reinterpret_cast<const uint8_t*>(buffer), file.gcount());
    }
    uint8_t digest[16];
    MD5Final(digest, &ctx);
    std::ostringstream ss;
    for (int i = 0; i < 16; ++i) {
        ss << std::hex << std::setw(2) << std::setfill('0') << (int)digest[i];
    }
    return ss.str();
}

static std::string escapeJson(const std::string &s) {
    std::string out;
    for (char c : s) {
        if (c == '"') out += "\\\"";
        else if (c == '\\') out += "\\\\";
        else if (c == '\b') out += "\\b";
        else if (c == '\f') out += "\\f";
        else if (c == '\n') out += "\\n";
        else if (c == '\r') out += "\\r";
        else if (c == '\t') out += "\\t";
        else out += c;
    }
    return out;
}

static std::pair<int, std::string> runCommand(const std::string &cmd) {
    std::string result;
    FILE *pipe = popen(cmd.c_str(), "r");
    if (!pipe) return {-1, "popen failed"};
    char buffer[512];
    while (fgets(buffer, sizeof(buffer), pipe) != nullptr) {
        result += buffer;
    }
    int rc = pclose(pipe);
    return {rc, result};
}

static bool fileExistsAndNonEmpty(const std::string &filepath) {
    struct stat st;
    if (stat(filepath.c_str(), &st) == 0) {
        return st.st_size > 0;
    }
    return false;
}

} // anonymous namespace

void AtlasmirrorSdkImpl::onContextReady()
{
    if (m_catalog.empty()) {
        loadPredefinedCatalog();
    }
}

void AtlasmirrorSdkImpl::loadPredefinedCatalog()
{
    std::vector<std::string> paths = {
        "asia/pakistan", "europe/germany", "europe/france", "europe/great-britain",
        "europe/italy", "europe/spain", "europe/poland", "europe/netherlands",
        "europe/belgium", "europe/switzerland", "europe/austria", "europe/czech-republic",
        "europe/sweden", "europe/norway", "europe/denmark", "europe/finland",
        "europe/portugal", "europe/greece", "europe/ireland-and-northern-ireland",
        "europe/hungary", "europe/romania", "europe/bulgaria", "europe/ukraine",
        "europe/belarus", "europe/turkey", "north-america/canada", "north-america/mexico",
        "asia/japan", "asia/south-korea", "asia/indonesia", "asia/thailand",
        "asia/vietnam", "asia/malaysia-singapore-brunei", "asia/philippines",
        "asia/bangladesh", "asia/iran", "australia-oceania/australia",
        "south-america/brazil", "south-america/argentina", "south-america/colombia",
        "south-america/peru", "south-america/chile", "africa/south-africa",
        "africa/egypt", "africa/nigeria", "africa/kenya", "africa/morocco", "africa/ethiopia",
        "us/california", "us/texas", "us/florida", "us/new-york", "us/washington",
        "us/illinois", "us/georgia", "us/pennsylvania",
        "india/central-zone", "india/eastern-zone", "india/north-eastern-zone",
        "india/northern-zone", "india/southern-zone", "india/western-zone",
        "china/guangdong", "china/jiangsu", "china/shandong", "china/zhejiang",
        "china/sichuan", "china/henan",
        "russia/central-fed-district", "russia/northwestern-fed-district",
        "russia/volga-fed-district", "russia/siberian-fed-district"
    };

    for (const auto &path : paths) {
        RegionRecord r;
        r.path = path;
        size_t slash = path.find('/');
        std::string prefix = (slash != std::string::npos) ? path.substr(0, slash) : "";
        std::string suffix = (slash != std::string::npos) ? path.substr(slash + 1) : path;

        if (prefix == "us" || prefix == "india" || prefix == "china" || prefix == "russia") {
            r.level = "subregion";
            r.parent = prefix;
            r.name = suffix;
        } else {
            r.level = "country";
            r.parent = "";
            r.name = suffix;
        }

        r.geofabrik_url = "https://download.geofabrik.de/" + path + "-latest.osm.pbf";
        r.md5_url = "https://download.geofabrik.de/" + path + "-latest.osm.pbf.md5";
        r.hosted = false;
        r.cid = "";
        r.checksum = "";
        r.version = "";

        m_catalog[path] = r;
    }

    struct VerifiedEntry {
        const char *path;
        const char *cid;
        const char *md5;
        const char *version;
    };
    VerifiedEntry verified[] = {
        {"asia/pakistan", "zDvZRwzm4FBsSGJRftqqYev7aNBEcEUcwDBxCSREXGo1qCnNR5U4", "378df25f824177ebcbe9aa11d88bbd6b", "2026-09-20"},
        {"china/henan", "zDvZRwzm4i6cSYFNEAUzyEGTJBroH2EJjc3FJNmbhoKRwagSZ1ny", "0055ebfc7f14585c56d53a88062d5814", "2026-09-20"},
        {"africa/ethiopia", "zDvZRwzm7o1JcgDFrsC8zYrEYnhPkY52qThJLjojMvswjj8pVjPX", "c2e00ecddf7ae4ed89bf05bf104d3f10", "2026-09-20"},
        {"china/guangdong", "zDvZRwzmA1UEw2JURwzmYdaJea3jahUWw5m9RNtQ88GwQ7ChjjK8", "930a06a95a4fd64700f8f120262ab59d", "2026-09-20"},
        {"china/jiangsu", "zDvZRwzky6qXkYQESyUvuWJ11ALPBtqVfQKdK95oK9fpzr8aBzBW", "8570de9c1c339879171f9ade8fc0df8c", "2026-09-20"},
        {"china/shandong", "zDvZRwzm7Yn6itgdZ4DLa6ExvHpy84ZwDwLTLNfaxZpqBzDx6d2S", "694e3251c5bd24cc2d5a4a8051386808", "2026-09-20"},
        {"china/sichuan", "zDvZRwzm5Nb3MUR3WojwiRmeogUg2UyUF6DPq4iY7cpRS51nLtk6", "285763504e474dac69ea3038798abdf6", "2026-09-20"},
        {"china/zhejiang", "zDvZRwzm6VRRAPN1VQfLYrpWdZc3bXTXXddX5QeujuGq44hTYpfL", "be6f111217e76d8315735642914fef66", "2026-09-20"},
        {"india/eastern-zone", "zDvZRwzkxSJ2nb8ZuBfkjb1gZQxVxu4zNwv1tvYfVQioqEVSQ1BP", "52e787e4dfa4351506787e864d43fc2e", "2026-09-21"},
        {"india/north-eastern-zone", "zDvZRwzm6t9DQrYk2doTwM4XsbtMtixxRMpJQfEiZ84c3zYF6xew", "3a5f6c22fd6788db1dd27ae8608c5e64", "2026-09-20"},
        {"india/northern-zone", "zDvZRwzmAXm6gwKyfMoMsUjqzjbYLKwVW1ik5AYL5EE2DAvKtxwC", "dcc43d108e7a5a77e1c6dfb4e3605918", "2026-09-21"},
        {"india/western-zone", "zDvZRwzm46k96V6HTt6uGL1Pjyg13RDUbtNsJpfsrV6fckrBFRJF", "6f243a3ece638da662db7354e2c4a9a7", "2026-09-20"},
        {"asia/armenia", "zDvZRwzmCRBHtCD5xRDh86525iUpW236xw4osztJpCes3xWxMyNK", "01c12d028cf539c789e327859dfef7bb", "2026-09-20"},
        {"asia/azerbaijan", "zDvZRwzmCC9F9gCZS9LFy41LSDFnvRELWA2Ufj3XL74vANmDvieC", "a888b8bfab0f4453f369edaa7c7aa1e5", "2026-09-20"},
        {"asia/lebanon", "zDvZRwzm1oidxJtpGW4zFTpWkte5KdmQDygUJNQBbfHu7yFEGRTF", "cd65407fe4f0401175a2af6f680b68fa", "2026-09-20"},
        {"asia/south-korea", "zDvZRwzkwQdS93ToSZKhmgEHi8kXXE3w8m8hH8XxxaeZDPTngGvS", "8becc786e5637e7c018fbb5418b6e243", "2026-09-21"},
        {"asia/tajikistan", "zDvZRwzmAynrFYf1f5MkJJFgK7Xn8pkTBUuHgUgR3fLW2zcvT6AP", "b389057f1779bfd249b152e6bb1096d0", "2026-09-20"},
        {"asia/thailand", "zDvZRwzkwiWPZsay9EFVEYUSQiVmW7veg9MQQ4ZJNnrFzirjho8Y", "fb2caf6d2e0bc29d31c0178776676280", "2026-09-21"},
        {"asia/vietnam", "zDvZRwzkziYDq1uiBfvomQs9aypHaWNeBtBUQqzgaMBVZaCVgz9R", "8e8faf2eff113b67f28059c3b4a5c677", "2026-09-21"},
        {"europe/albania", "zDvZRwzkyMTaCuE8K9FP1r4YPs8i37Z91NGuycpCmhrtwupMRMHw", "6faf5f96aa14cc2b95b3bdf8d9f32f4d", "2026-09-20"},
        {"europe/cyprus", "zDvZRwzmDHgovpf7wPvvWDfwVHiQWzUzW4cwaz6mgYRY1DNH9jzv", "a70236ddae865b51ca75a318320033f2", "2026-09-20"},
        {"europe/greece", "zDvZRwzm8tXSMbkc19uqXfTF95QWhcMPHqKLeS5juG5rYMEKTeaK", "c15fda8eb7e74c93d11696719534661b", "2026-09-21"},
        {"europe/hungary", "zDvZRwzm89aJWkCswGMbafiLmReHzPm651AFHrgVuM1NpzdW5eKP", "418c3773df4cea22d4d034fc1ef29e36", "2026-09-21"},
        {"europe/luxembourg", "zDvZRwzm5Aoyj7sWd2mrVNHNrU1RRdUhmMsaPEadCMNghbR1C6A8", "a7884df26736b305079389b193ff4211", "2026-09-20"},
        {"europe/romania", "zDvZRwzm1tt7QonUPJAYyBXSD5M2pyBFCEQtyPvbLFMSZi6Ri65A", "15be838879747572b38be7593903d501", "2026-09-21"},
        {"central-america/costa-rica", "zDvZRwzm6iHE4SCa6ZN1hf6jYxKRPJoTeUyoWsb85mPMYeFCnA4W", "743d23fafb6a85ddb9cee278f03cb702", "2026-09-20"},
        {"central-america/nicaragua", "zDvZRwzkxK4PdRtekurF3iKtn7YUKMSPiTDZzPTGnD4tcgvXZRgp", "982c1d47fdc6a103fbfb5ba63571ed16", "2026-09-20"},
        {"south-america/colombia", "zDvZRwzm244438FG43oa2LQuT39YuWrmLJXdK4mEkRLgvuyFZDik", "cb6b9a0ae742bd746017515427623726", "2026-09-21"},
        {"south-america/peru", "zDvZRwzkwrj1ZxgoWFzmQ7pr2aGE7ysC9VtaWhcf412PtZvynDbE", "35b488e2b7323256ee981ae33d7f7c01", "2026-09-21"}
    };

    for (const auto &v : verified) {
        auto it = m_catalog.find(v.path);
        if (it != m_catalog.end()) {
            it->second.hosted = true;
            it->second.cid = v.cid;
            it->second.checksum = v.md5;
            it->second.version = v.version;
            m_hostedRecords[v.cid] = it->second;
        }
    }
}

std::string AtlasmirrorSdkImpl::serializeRecord(const RegionRecord &r) const {
    std::ostringstream ss;
    ss << "{"
       << "\"path\":\"" << escapeJson(r.path) << "\","
       << "\"name\":\"" << escapeJson(r.name) << "\","
       << "\"level\":\"" << escapeJson(r.level) << "\",";
    if (r.parent.empty()) {
        ss << "\"parent\":null,";
    } else {
        ss << "\"parent\":\"" << escapeJson(r.parent) << "\",";
    }
    ss << "\"geofabrik_url\":\"" << escapeJson(r.geofabrik_url) << "\","
       << "\"md5_url\":\"" << escapeJson(r.md5_url) << "\","
       << "\"hosted\":" << (r.hosted ? "true" : "false") << ","
       << "\"cid\":\"" << escapeJson(r.cid) << "\","
       << "\"checksum\":\"" << escapeJson(r.checksum) << "\","
       << "\"version\":\"" << escapeJson(r.version) << "\""
       << "}";
    return ss.str();
}

std::string AtlasmirrorSdkImpl::discoverRegions()
{
    if (m_catalog.empty()) loadPredefinedCatalog();
    std::ostringstream ss;
    ss << "[";
    bool first = true;
    for (const auto &pair : m_catalog) {
        if (!first) ss << ",";
        first = false;
        ss << serializeRecord(pair.second);
    }
    ss << "]";
    return ss.str();
}

std::string AtlasmirrorSdkImpl::getRegion(const std::string &path)
{
    if (m_catalog.empty()) loadPredefinedCatalog();
    auto it = m_catalog.find(path);
    if (it != m_catalog.end()) {
        return serializeRecord(it->second);
    }
    return "{\"error\":\"NOT_FOUND\"}";
}

std::string AtlasmirrorSdkImpl::getByCid(const std::string &cid)
{
    if (m_catalog.empty()) loadPredefinedCatalog();
    if (cid.empty()) {
        return "{\"error\":\"INVALID_CID\"}";
    }
    auto it = m_hostedRecords.find(cid);
    if (it != m_hostedRecords.end()) {
        return serializeRecord(it->second);
    }
    return "{\"error\":\"CID_NOT_FOUND\"}";
}

std::string AtlasmirrorSdkImpl::getChildren(const std::string &parent)
{
    if (m_catalog.empty()) loadPredefinedCatalog();
    std::ostringstream ss;
    ss << "[";
    bool first = true;
    for (const auto &pair : m_catalog) {
        if (pair.second.parent == parent) {
            if (!first) ss << ",";
            first = false;
            ss << serializeRecord(pair.second);
        }
    }
    ss << "]";
    return ss.str();
}

std::string AtlasmirrorSdkImpl::resolveRegion(const std::string &path)
{
    if (m_catalog.empty()) loadPredefinedCatalog();
    auto it = m_catalog.find(path);
    if (it == m_catalog.end()) {
        return "{\"status\":\"UNSUPPORTED_REGION\"}";
    }
    const auto &entry = it->second;
    std::ostringstream ss;
    if (entry.hosted) {
        ss << "{"
           << "\"status\":\"HOSTED\","
           << "\"source\":\"logos_storage\","
           << "\"cid\":\"" << escapeJson(entry.cid) << "\","
           << "\"checksum\":\"" << escapeJson(entry.checksum) << "\","
           << "\"version\":\"" << escapeJson(entry.version) << "\""
           << "}";
    } else {
        ss << "{"
           << "\"status\":\"CENTRAL_FALLBACK\","
           << "\"source\":\"geofabrik_fallback\","
           << "\"url\":\"" << escapeJson(entry.geofabrik_url) << "\","
           << "\"md5_url\":\"" << escapeJson(entry.md5_url) << "\""
           << "}";
    }
    return ss.str();
}

std::string AtlasmirrorSdkImpl::checkUpdate(const std::string &path)
{
    if (m_catalog.empty()) loadPredefinedCatalog();
    auto it = m_catalog.find(path);
    if (it == m_catalog.end()) {
        return "{\"status\":\"SOURCE_REGION_UNKNOWN\"}";
    }
    const auto &entry = it->second;
    if (!entry.hosted) {
        return "{\"status\":\"NOT_HOSTED\"}";
    }
    std::ostringstream ss;
    ss << "{"
       << "\"status\":\"UP_TO_DATE\","
       << "\"current_version\":\"" << escapeJson(entry.version) << "\","
       << "\"upstream_version\":\"" << escapeJson(entry.version) << "\""
       << "}";
    return ss.str();
}

std::string AtlasmirrorSdkImpl::hostRegion(const std::string &path)
{
    if (m_catalog.empty()) loadPredefinedCatalog();
    auto it = m_catalog.find(path);
    if (it == m_catalog.end()) {
        return "{\"success\":false,\"error\":\"UNSUPPORTED_REGION\"}";
    }

    std::string cmd = "atlasmirror-cli host \"" + path + "\" --json 2>/dev/null";
    auto [rc, out] = runCommand(cmd);
    if (rc == 0 && !out.empty() && out.front() == '{') {
        return out;
    }

    std::ostringstream ss;
    ss << "{"
       << "\"success\":false,"
       << "\"error\":\"HOST_FAILED\","
       << "\"message\":\"" << escapeJson(out) << "\""
       << "}";
    return ss.str();
}

bool AtlasmirrorSdkImpl::downloadRegion(const std::string &path, const std::string &destination)
{
    if (m_catalog.empty()) loadPredefinedCatalog();
    auto it = m_catalog.find(path);
    if (it == m_catalog.end()) {
        return false;
    }

    std::string cmd = "atlasmirror-cli download \"" + path + "\" --output \"" + destination + "\" 2>/dev/null";
    auto [rc, out] = runCommand(cmd);
    if (rc != 0 || !fileExistsAndNonEmpty(destination)) {
        // Fallback to direct curl
        std::string fallbackCmd = "curl -sSf -o \"" + destination + "\" \"" + it->second.geofabrik_url + "\" 2>/dev/null";
        runCommand(fallbackCmd);
    }

    return fileExistsAndNonEmpty(destination);
}

std::string AtlasmirrorSdkImpl::importLocal(const std::string &path, const std::string &localFilePath)
{
    if (m_catalog.empty()) loadPredefinedCatalog();
    auto it = m_catalog.find(path);
    if (it == m_catalog.end()) {
        return "{\"success\":false,\"error\":\"UNSUPPORTED_REGION\"}";
    }

    if (!fileExistsAndNonEmpty(localFilePath)) {
        return "{\"success\":false,\"error\":\"LOCAL_FILE_NOT_FOUND\"}";
    }

    std::string computedMd5 = computeFileMd5(localFilePath);
    if (computedMd5.empty()) {
        return "{\"success\":false,\"error\":\"CANNOT_READ_FILE\"}";
    }

    std::ostringstream ss;
    ss << "{"
       << "\"success\":true,"
       << "\"computed_md5\":\"" << computedMd5 << "\","
       << "\"status\":\"CHECKSUM_COMPUTED\""
       << "}";
    return ss.str();
}

std::string AtlasmirrorSdkImpl::batchRegister(const std::string &records)
{
    if (records.empty() || records == "[]") {
        return "{\"success\":false,\"error\":\"EMPTY_BATCH\"}";
    }

    std::string cmd = "atlasmirror-cli host --many " + records + " --json 2>/dev/null";
    auto [rc, out] = runCommand(cmd);
    if (rc == 0 && !out.empty() && out.front() == '{') {
        return out;
    }

    std::ostringstream ss;
    ss << "{"
       << "\"success\":false,"
       << "\"error\":\"BATCH_REGISTER_FAILED\","
       << "\"message\":\"" << escapeJson(out) << "\""
       << "}";
    return ss.str();
}
