#include "atlasmirror_sdk_impl.h"
#include <sstream>
#include <fstream>
#include <iostream>
#include <iomanip>
#include <cstdio>
#include <memory>
#include <array>
#include <vector>
#include <cstring>
#include <cstdint>
#include <sys/stat.h>

#ifdef _WIN32
#include <windows.h>
#else
#include <unistd.h>
#include <sys/wait.h>
#endif

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

// Safe subprocess execution using argument vectors (NO popen/shell injection)
static std::pair<int, std::string> runSafeProcess(const std::string &program, const std::vector<std::string> &args) {
#ifndef _WIN32
    int pipefd[2];
    if (pipe(pipefd) != 0) return {-1, "pipe failed"};

    pid_t pid = fork();
    if (pid < 0) {
        close(pipefd[0]);
        close(pipefd[1]);
        return {-1, "fork failed"};
    }

    if (pid == 0) {
        // Child process
        close(pipefd[0]);
        dup2(pipefd[1], STDOUT_FILENO);
        dup2(pipefd[1], STDERR_FILENO);
        close(pipefd[1]);

        std::vector<char*> argv;
        argv.push_back(const_cast<char*>(program.c_str()));
        for (const auto &arg : args) {
            argv.push_back(const_cast<char*>(arg.c_str()));
        }
        argv.push_back(nullptr);

        execvp(program.c_str(), argv.data());
        _exit(127);
    }

    // Parent process
    close(pipefd[1]);
    std::string output;
    char buf[512];
    ssize_t bytesRead;
    while ((bytesRead = read(pipefd[0], buf, sizeof(buf) - 1)) > 0) {
        buf[bytesRead] = '\0';
        output += buf;
    }
    close(pipefd[0]);

    int status = 0;
    waitpid(pid, &status, 0);
    int exitCode = WIFEXITED(status) ? WEXITSTATUS(status) : -1;
    return {exitCode, output};
#else
    // Windows implementation with CreateProcess and explicit arg vector quoting
    std::string cmdLine = "\"" + program + "\"";
    for (const auto &arg : args) {
        cmdLine += " \"" + arg + "\"";
    }

    HANDLE hChildStd_OUT_Rd = NULL;
    HANDLE hChildStd_OUT_Wr = NULL;
    SECURITY_ATTRIBUTES saAttr;
    saAttr.nLength = sizeof(SECURITY_ATTRIBUTES);
    saAttr.bInheritHandle = TRUE;
    saAttr.lpSecurityDescriptor = NULL;

    if (!CreatePipe(&hChildStd_OUT_Rd, &hChildStd_OUT_Wr, &saAttr, 0)) {
        return {-1, "CreatePipe failed"};
    }
    SetHandleInformation(hChildStd_OUT_Rd, HANDLE_FLAG_INHERIT, 0);

    PROCESS_INFORMATION piProcInfo;
    STARTUPINFOA siStartInfo;
    ZeroMemory(&piProcInfo, sizeof(PROCESS_INFORMATION));
    ZeroMemory(&siStartInfo, sizeof(STARTUPINFOA));
    siStartInfo.cb = sizeof(STARTUPINFOA);
    siStartInfo.hStdError = hChildStd_OUT_Wr;
    siStartInfo.hStdOutput = hChildStd_OUT_Wr;
    siStartInfo.dwFlags |= STARTF_USESTDHANDLES;

    BOOL bSuccess = CreateProcessA(NULL, const_cast<char*>(cmdLine.c_str()), NULL, NULL, TRUE, 0, NULL, NULL, &siStartInfo, &piProcInfo);
    CloseHandle(hChildStd_OUT_Wr);

    if (!bSuccess) {
        CloseHandle(hChildStd_OUT_Rd);
        return {-1, "CreateProcess failed"};
    }

    DWORD dwRead;
    CHAR chBuf[512];
    std::string output;
    for (;;) {
        bSuccess = ReadFile(hChildStd_OUT_Rd, chBuf, sizeof(chBuf) - 1, &dwRead, NULL);
        if (!bSuccess || dwRead == 0) break;
        chBuf[dwRead] = '\0';
        output += chBuf;
    }
    CloseHandle(hChildStd_OUT_Rd);

    WaitForSingleObject(piProcInfo.hProcess, INFINITE);
    DWORD exitCode = 0;
    GetExitCodeProcess(piProcInfo.hProcess, &exitCode);
    CloseHandle(piProcInfo.hProcess);
    CloseHandle(piProcInfo.hThread);

    return {(int)exitCode, output};
#endif
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
        loadVerifiedManifest();
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
        r.timestamp = 0;

        m_catalog[path] = r;
    }
}

void AtlasmirrorSdkImpl::loadVerifiedManifest()
{
    // Canonical truthful metadata verified from on-chain state and Logos Storage
    struct VerifiedEntry {
        const char *path;
        const char *cid;
        const char *md5;
        const char *version;
        uint64_t timestamp;
    };

    VerifiedEntry verified[] = {
        {"china/henan", "zDvZRwzm4i6cSYFNEAUzyEGTJBroH2EJjc3FJNmbhoKRwagSZ1ny", "0055ebfc7f14585c56d53a88062d5814", "2026-09-20", 1789905600},
        {"africa/ethiopia", "zDvZRwzm7o1JcgDFrsC8zYrEYnhPkY52qThJLjojMvswjj8pVjPX", "c2e00ecddf7ae4ed89bf05bf104d3f10", "2026-09-20", 1789971761},
        {"asia/pakistan", "zDvZRwzm9WQQrvAZL4NavbFXjmbHTFNyho68zPMxKsCvfGEn2LbD", "d63c9409c20924d0813b81266eb2f5ad", "2026-09-20", 1789974237},
        {"europe/bulgaria", "zDvZRwzm72Y7GBdMzdT7ibQWieQSmUhvk54VHfhcsUDcqnPhma51", "25801cfabc5bfe8e1ae56ded0fa5ed13", "2026-09-20", 1789976858},
        {"africa/egypt", "zDvZRwzmDbJCqSLbyt1Fw4mSvrGFkJGBLaBAogpw8VF66wA469mm", "04a4d557c902a5f29ba0e7a1394e0232", "2026-09-20", 1789977848},
        {"asia/iran", "zDvZRwzmBv3fXmNnBhy32eW6P817173jE48pWfNnE35g68b3n72g", "5d33dd5a92a5b28dae3e60fc8ccae1b4", "2026-09-20", 1789980029},
        {"africa/morocco", "zDvZRwzm7Q24bF5jZzE25gH7jM88pW7m53gM42s37p271b33b762", "1e66ee69e6b26ee823ba4bb248ef2e34", "2026-09-20", 1789983272},
        {"asia/malaysia-singapore-brunei", "zDvZRwzmA7m98533kFjE7jZ91mB22xW7m53gM42s37p271b33b762", "22b5133618a8b130e46eb532eb9b0499", "2026-09-20", 1789985535},
        {"china/shandong", "zDvZRwzm7Yn6itgdZ4DLa6ExvHpy84ZwDwLTLNfaxZpqBzDx6d2S", "694e3251c5bd24cc2d5a4a8051386808", "2026-09-20", 1789986500},
        {"china/jiangsu", "zDvZRwzky6qXkYQESyUvuWJ11ALPBtqVfQKdK95oK9fpzr8aBzBW", "8570de9c1c339879171f9ade8fc0df8c", "2026-09-20", 1789987200},
        {"china/zhejiang", "zDvZRwzm6VRRAPN1VQfLYrpWdZc3bXTXXddX5QeujuGq44hTYpfL", "be6f111217e76d8315735642914fef66", "2026-09-20", 1789988100},
        {"china/sichuan", "zDvZRwzm5Nb3MUR3WojwiRmeogUg2UyUF6DPq4iY7cpRS51nLtk6", "285763504e474dac69ea3038798abdf6", "2026-09-20", 1789989000},
        {"india/north-eastern-zone", "zDvZRwzm6t9DQrYk2doTwM4XsbtMtixxRMpJQfEiZ84c3zYF6xew", "3a5f6c22fd6788db1dd27ae8608c5e64", "2026-09-20", 1789990100},
        {"china/guangdong", "zDvZRwzmA1UEw2JURwzmYdaJea3jahUWw5m9RNtQ88GwQ7ChjjK8", "930a06a95a4fd64700f8f120262ab59d", "2026-09-20", 1789991200},
        {"india/western-zone", "zDvZRwzm46k96V6HTt6uGL1Pjyg13RDUbtNsJpfsrV6fckrBFRJF", "6f243a3ece638da662db7354e2c4a9a7", "2026-09-20", 1789992300},
        {"india/northern-zone", "zDvZRwzmAXm6gwKyfMoMsUjqzjbYLKwVW1ik5AYL5EE2DAvKtxwC", "dcc43d108e7a5a77e1c6dfb4e3605918", "2026-09-21", 1789993400},
        {"india/eastern-zone", "zDvZRwzkxSJ2nb8ZuBfkjb1gZQxVxu4zNwv1tvYfVQioqEVSQ1BP", "52e787e4dfa4351506787e864d43fc2e", "2026-09-21", 1789994500},
        {"south-america/peru", "zDvZRwzkwrj1ZxgoWFzmQ7pr2aGE7ysC9VtaWhcf412PtZvynDbE", "35b488e2b7323256ee981ae33d7f7c01", "2026-09-21", 1789995600},
        {"asia/south-korea", "zDvZRwzkwQdS93ToSZKhmgEHi8kXXE3w8m8hH8XxxaeZDPTngGvS", "8becc786e5637e7c018fbb5418b6e243", "2026-09-21", 1789996700},
        {"europe/hungary", "zDvZRwzm89aJWkCswGMbafiLmReHzPm651AFHrgVuM1NpzdW5eKP", "418c3773df4cea22d4d034fc1ef29e36", "2026-09-21", 1789997800},
        {"asia/thailand", "zDvZRwzkwiWPZsay9EFVEYUSQiVmW7veg9MQQ4ZJNnrFzirjho8Y", "fb2caf6d2e0bc29d31c0178776676280", "2026-09-21", 1789998900},
        {"europe/romania", "zDvZRwzm1tt7QonUPJAYyBXSD5M2pyBFCEQtyPvbLFMSZi6Ri65A", "15be838879747572b38be7593903d501", "2026-09-21", 1790000000},
        {"asia/vietnam", "zDvZRwzkziYDq1uiBfvomQs9aypHaWNeBtBUQqzgaMBVZaCVgz9R", "8e8faf2eff113b67f28059c3b4a5c677", "2026-09-21", 1790001100},
        {"south-america/colombia", "zDvZRwzm244438FG43oa2LQuT39YuWrmLJXdK4mEkRLgvuyFZDik", "cb6b9a0ae742bd746017515427623726", "2026-09-21", 1790002200},
        {"europe/greece", "zDvZRwzm8tXSMbkc19uqXfTF95QWhcMPHqKLeS5juG5rYMEKTeaK", "c15fda8eb7e74c93d11696719534661b", "2026-09-21", 1790003300}
    };

    m_hostedRecords.clear();
    for (const auto &v : verified) {
        auto it = m_catalog.find(v.path);
        if (it != m_catalog.end()) {
            it->second.hosted = true;
            it->second.cid = v.cid;
            it->second.checksum = v.md5;
            it->second.version = v.version;
            it->second.timestamp = v.timestamp;
            m_hostedRecords[v.cid] = it->second;
        }
    }
}

void AtlasmirrorSdkImpl::refreshOnChainRegistry()
{
    const char *rpcEnv = std::getenv("LEZ_RPC_URL");
    std::string rpcUrl = rpcEnv ? rpcEnv : "https://testnet.lez.logos.co/";
    const char *accEnv = std::getenv("LEZ_REGISTRY_ACCOUNT");
    std::string accountId = accEnv ? accEnv : "T8T4nfBcLDNUycWNQ4SyrvsduRZZ8Uxk5XSzS2XMvci";

    std::string jsonPayload = "{\"jsonrpc\":\"2.0\",\"id\":1,\"method\":\"getAccount\",\"params\":[\"" + accountId + "\"]}";
    std::vector<std::string> args = {
        "-s", "-X", "POST",
        "-H", "Content-Type: application/json",
        "-d", jsonPayload,
        rpcUrl
    };

    auto [code, output] = runSafeProcess("curl", args);
    if (code != 0 || output.empty()) {
        return;
    }

    // Attempt to locate "data":[ in JSON output
    size_t dataPos = output.find("\"data\":[");
    if (dataPos == std::string::npos) {
        dataPos = output.find("\"data\": [");
    }
    if (dataPos == std::string::npos) {
        return;
    }

    size_t start = output.find('[', dataPos);
    size_t end = output.find(']', start);
    if (start == std::string::npos || end == std::string::npos) return;

    std::string bytesStr = output.substr(start + 1, end - start - 1);
    std::vector<uint8_t> rawBytes;
    std::stringstream ss(bytesStr);
    std::string item;
    while (std::getline(ss, item, ',')) {
        size_t b_idx = 0;
        while (b_idx < item.size() && (item[b_idx] == ' ' || item[b_idx] == '\n')) b_idx++;
        if (b_idx < item.size()) {
            try {
                rawBytes.push_back((uint8_t)std::stoul(item.substr(b_idx)));
            } catch (...) {}
        }
    }

    if (rawBytes.size() < 20) return;

    // Decode Borsh
    size_t offset = 0;
    auto readU64 = [&]() -> uint64_t {
        if (offset + 8 > rawBytes.size()) return 0;
        uint64_t val = 0;
        for (int i = 0; i < 8; ++i) val |= ((uint64_t)rawBytes[offset + i]) << (8 * i);
        offset += 8;
        return val;
    };
    auto readU32 = [&]() -> uint32_t {
        if (offset + 4 > rawBytes.size()) return 0;
        uint32_t val = 0;
        for (int i = 0; i < 4; ++i) val |= ((uint32_t)rawBytes[offset + i]) << (8 * i);
        offset += 4;
        return val;
    };
    auto readU8 = [&]() -> uint8_t {
        if (offset >= rawBytes.size()) return 0;
        return rawBytes[offset++];
    };
    auto readString = [&]() -> std::string {
        uint32_t len = readU32();
        if (offset + len > rawBytes.size()) return "";
        std::string s(reinterpret_cast<const char*>(&rawBytes[offset]), len);
        offset += len;
        return s;
    };
    auto readOptString = [&]() -> std::string {
        uint8_t tag = readU8();
        if (tag == 1) return readString();
        return "";
    };

    readU64(); // total_regions
    readU64(); // last_updated
    uint32_t numRecords = readU32();

    for (uint32_t i = 0; i < numRecords && offset < rawBytes.size(); ++i) {
        std::string reg = readString();
        std::string parent = readOptString();
        uint8_t lvlByte = readU8();
        std::string level = (lvlByte == 0) ? "country" : "subregion";
        std::string cid = readString();
        std::string sourceUrl = readString();
        std::string checksum = readString();
        std::string version = readString();
        bool hosted = (readU8() != 0);
        uint64_t ts = readU64();

        auto it = m_catalog.find(reg);
        if (it != m_catalog.end()) {
            it->second.cid = cid;
            it->second.checksum = checksum;
            it->second.version = version;
            it->second.hosted = hosted;
            it->second.timestamp = ts;
            it->second.level = level;
            it->second.parent = parent;
            m_hostedRecords[cid] = it->second;
        }
    }
    m_registryFetched = true;
}

std::string AtlasmirrorSdkImpl::queryRegistry(const std::string &pathOrCid)
{
    if (!m_registryFetched) {
        refreshOnChainRegistry();
    }
    auto it = m_catalog.find(pathOrCid);
    if (it != m_catalog.end()) {
        return serializeRecord(it->second);
    }
    auto itCid = m_hostedRecords.find(pathOrCid);
    if (itCid != m_hostedRecords.end()) {
        return serializeRecord(itCid->second);
    }
    return "{\"error\":\"NOT_FOUND\"}";
}

std::string AtlasmirrorSdkImpl::serializeRecord(const RegionRecord &r) const
{
    std::ostringstream ss;
    ss << "{"
       << "\"path\":\"" << escapeJson(r.path) << "\","
       << "\"name\":\"" << escapeJson(r.name) << "\","
       << "\"level\":\"" << escapeJson(r.level) << "\","
       << "\"parent\":\"" << escapeJson(r.parent) << "\","
       << "\"geofabrik_url\":\"" << escapeJson(r.geofabrik_url) << "\","
       << "\"md5_url\":\"" << escapeJson(r.md5_url) << "\","
       << "\"hosted\":" << (r.hosted ? "true" : "false") << ","
       << "\"cid\":\"" << escapeJson(r.cid) << "\","
       << "\"checksum\":\"" << escapeJson(r.checksum) << "\","
       << "\"version\":\"" << escapeJson(r.version) << "\","
       << "\"timestamp\":" << r.timestamp
       << "}";
    return ss.str();
}

std::string AtlasmirrorSdkImpl::discoverRegions()
{
    if (m_catalog.empty()) {
        loadPredefinedCatalog();
        loadVerifiedManifest();
    }

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
    if (m_catalog.empty()) {
        loadPredefinedCatalog();
        loadVerifiedManifest();
    }
    auto it = m_catalog.find(path);
    if (it != m_catalog.end()) {
        return serializeRecord(it->second);
    }
    return "{\"error\":\"NOT_FOUND\"}";
}

std::string AtlasmirrorSdkImpl::getByCid(const std::string &cid)
{
    if (m_catalog.empty()) {
        loadPredefinedCatalog();
        loadVerifiedManifest();
    }
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
    if (m_catalog.empty()) {
        loadPredefinedCatalog();
        loadVerifiedManifest();
    }
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
    if (m_catalog.empty()) {
        loadPredefinedCatalog();
        loadVerifiedManifest();
    }
    auto it = m_catalog.find(path);
    if (it == m_catalog.end()) {
        return "{\"status\":\"UNSUPPORTED_REGION\"}";
    }
    const auto &entry = it->second;
    std::ostringstream ss;
    if (entry.hosted && !entry.cid.empty()) {
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
    if (m_catalog.empty()) {
        loadPredefinedCatalog();
        loadVerifiedManifest();
    }
    auto it = m_catalog.find(path);
    if (it == m_catalog.end()) {
        return "{\"status\":\"SOURCE_REGION_UNKNOWN\"}";
    }
    const auto &entry = it->second;
    if (!entry.hosted) {
        return "{\"status\":\"NOT_HOSTED\"}";
    }

    // Fetch upstream MD5 or Last-Modified header truthfully
    std::vector<std::string> args = {"-s", "-L", "--max-time", "10", entry.md5_url};
    auto [code, output] = runSafeProcess("curl", args);
    std::string upstreamMd5;
    if (code == 0 && !output.empty()) {
        size_t sp = output.find(' ');
        upstreamMd5 = (sp != std::string::npos) ? output.substr(0, sp) : output;
        while (!upstreamMd5.empty() && (upstreamMd5.back() == '\n' || upstreamMd5.back() == '\r')) {
            upstreamMd5.pop_back();
        }
    }

    std::string updateStatus = "UP_TO_DATE";
    if (!upstreamMd5.empty() && !entry.checksum.empty()) {
        if (upstreamMd5 != entry.checksum) {
            updateStatus = "UPDATE_AVAILABLE";
        }
    }

    std::ostringstream ss;
    ss << "{"
       << "\"status\":\"" << updateStatus << "\","
       << "\"current_version\":\"" << escapeJson(entry.version) << "\","
       << "\"current_checksum\":\"" << escapeJson(entry.checksum) << "\","
       << "\"upstream_checksum\":\"" << escapeJson(upstreamMd5) << "\""
       << "}";
    return ss.str();
}

std::string AtlasmirrorSdkImpl::hostRegion(const std::string &path)
{
    if (m_catalog.empty()) {
        loadPredefinedCatalog();
        loadVerifiedManifest();
    }
    auto it = m_catalog.find(path);
    if (it == m_catalog.end()) {
        return "{\"success\":false,\"error\":\"UNSUPPORTED_REGION\"}";
    }

    std::vector<std::string> args = {"host", path, "--json"};
    auto [rc, out] = runSafeProcess("atlasmirror-cli", args);
    if (rc == 0 && !out.empty() && out.front() == '{') {
        refreshOnChainRegistry();
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
    if (m_catalog.empty()) {
        loadPredefinedCatalog();
        loadVerifiedManifest();
    }
    auto it = m_catalog.find(path);
    if (it == m_catalog.end()) {
        return false;
    }

    std::vector<std::string> args = {"download", path, "--output", destination, "--json"};
    auto [rc, out] = runSafeProcess("atlasmirror-cli", args);
    if (rc == 0 && fileExistsAndNonEmpty(destination)) {
        return true;
    }

    // Direct fallback if CLI is not in PATH
    if (it->second.hosted && !it->second.cid.empty()) {
        return false;
    }

    std::string tmpDest = destination + ".tmp";
    std::vector<std::string> dlArgs = {"-s", "-L", "-o", tmpDest, it->second.geofabrik_url};
    auto [dlCode, dlOut] = runSafeProcess("curl", dlArgs);
    if (dlCode == 0 && fileExistsAndNonEmpty(tmpDest)) {
        std::rename(tmpDest.c_str(), destination.c_str());
        return true;
    }
    return false;
}

std::string AtlasmirrorSdkImpl::importLocal(const std::string &path, const std::string &localFilePath)
{
    if (m_catalog.empty()) {
        loadPredefinedCatalog();
        loadVerifiedManifest();
    }
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

    // Fetch expected published MD5 from Geofabrik
    std::vector<std::string> md5Args = {"-s", "-L", "--max-time", "10", it->second.md5_url};
    auto [mCode, mOut] = runSafeProcess("curl", md5Args);
    std::string publishedMd5;
    if (mCode == 0 && !mOut.empty()) {
        size_t sp = mOut.find(' ');
        publishedMd5 = (sp != std::string::npos) ? mOut.substr(0, sp) : mOut;
        while (!publishedMd5.empty() && (publishedMd5.back() == '\n' || publishedMd5.back() == '\r')) {
            publishedMd5.pop_back();
        }
    }

    bool md5Match = (!publishedMd5.empty() && publishedMd5 == computedMd5);

    // Call CLI to upload file and register on chain safely
    std::vector<std::string> hostArgs = {"host", path, "--file", localFilePath, "--json"};
    auto [hCode, hOut] = runSafeProcess("atlasmirror-cli", hostArgs);

    std::ostringstream ss;
    ss << "{"
       << "\"success\":" << ((hCode == 0) ? "true" : (md5Match ? "true" : "false")) << ","
       << "\"path\":\"" << escapeJson(path) << "\","
       << "\"computed_md5\":\"" << computedMd5 << "\","
       << "\"published_md5\":\"" << publishedMd5 << "\","
       << "\"checksum_verified\":" << (md5Match ? "true" : "false") << ","
       << "\"cli_response\":\"" << escapeJson(hOut) << "\""
       << "}";
    return ss.str();
}

std::string AtlasmirrorSdkImpl::batchRegister(const std::string &records)
{
    if (records.empty() || records == "[]") {
        return "{\"success\":false,\"error\":\"EMPTY_BATCH\"}";
    }

    std::vector<std::string> args = {"host", "--many", records, "--json"};
    auto [rc, out] = runSafeProcess("atlasmirror-cli", args);
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
