#ifndef _DEFINED_HASHING_H
#define _DEFINED_HASHING_H

#ifdef _USE_IPP
class MD5Hash {
public:
  enum {
    HASHBYTES = 16
  };
  MD5Hash();
  ~MD5Hash();

  
  bool Init();
  bool Update(const void *datain, int size);
  bool Final(void* hash, int hashsize);

  static bool Compute(const void *datain, int size, void* hash, int hashsize);
  static bool Test();
  static void ComputeMD5InRounds(BYTE md5[HASHBYTES], uint32 rounds);
  static bool GetStr(const wchar_t* wszIn, char* data, int count);
  static bool GetStr(const wchar_t* wszIn, wchar_t* data, int count);

private:
  void *Context;
  
  void CloseContext();
};


class SHA256Hash {
public:
  enum {
    HASHBYTES = 32
  };
  SHA256Hash();
  ~SHA256Hash();

  bool Init();
  bool Update(const void *datain, int size);
  bool Final(void* hash, int hashsize);
  static bool Compute(const void *datain, int size, void* hash, int hashsize);
  static bool Test();
  static void ComputeSHAInRounds(BYTE md5[HASHBYTES], uint32 rounds);
  static bool GetStr(const wchar_t* wzsIn, char* data, int count);
  static bool GetStr(const wchar_t* wszIn, wchar_t* data, int count);

private:
  void *Context;
  
  void CloseContext();
};
#else
#define rol32(x, rotval) ((x << rotval) | (x >> (uint32)(32 - rotval)))
#define F(x, y, z) ((x & y) | (~x & z))
#define G(x, y, z) ((x & z) | (y & ~z))
#define H(x, y, z) (x ^ y ^ z)
#define I(x, y, z) (y ^ (x | ~z))
#define FUNC(T, a, b, c, d, x, s, ac) { (a) += T((b), (c), (d)) + (x) + (uint32)(ac); a = rol32((a), (s));  (a) += (b); }

class MD5Hash {
public:
  enum {
    CHUNK_SIZE = 8 * 1024,
    BLOCKSIZE = 0x40,
    HASHBYTES = 0x10,
    BLOCKMASK = BLOCKSIZE - 1
  };
  MD5Hash();

  static bool Compute(const void *datain, uint32 size, void* hash, uint32 hashsize);
  static bool ComputeFileHash(LPCTSTR wszFile, void* hash, uint32 hashsize);
  static bool GetStr(const wchar_t* wszIn, char* data, int count);
  static bool GetStr(const wchar_t* wszIn, wchar_t* data, int count);
  static bool Test();
  static void ComputeMD5InRounds(BYTE md5[HASHBYTES], uint32 rounds);


private:
  void Init();
  void Update(const void *input, uint32 len);
  void Final(BYTE hash[HASHBYTES]);
  void Perform(const BYTE block[BLOCKSIZE]);

  uint32 State[4];
  uint32 Count[2];
  BYTE Buffer[BLOCKSIZE];
};

#define ROTR32(n,x) ((x >> n) | (x << (32 - n)))

#define ch(x,y,z) ((x & y) ^ ((~x) & z))
#define maj(x,y,z) ((x & y) ^ (x & z) ^ (y & z))

#define bigsigma256_0(x)   (ROTR32(2,  x) ^ ROTR32(13, x) ^ ROTR32(22, x))
#define bigsigma256_1(x)   (ROTR32(6,  x) ^ ROTR32(11, x) ^ ROTR32(25, x))
#define smallsigma256_0(x) (ROTR32(7,  x) ^ ROTR32(18, x) ^ (x >> 3))
#define smallsigma256_1(x) (ROTR32(17, x) ^ ROTR32(19, x) ^ (x >> 10))

#define expand256x(W, i) (smallsigma256_1(W[(i-2)&15]) + W[(i-7)&15] + smallsigma256_0(W[(i-15)&15]) + W[i&15]) 
#define expand256(W, i)  (W[i&15] = expand256x(W, i))
#define subRound256(a,b,c,d,e,f,g,h,k,data) (h += bigsigma256_1(e) + ch(e, f, g) + k + data, d += h, h += bigsigma256_0(a) + maj(a,b,c))

class SHA256Hash {
public:
  enum {
    HASHWORDS  = 0x08,
    BLOCKWORDS = 0x10,
    HASHBYTES  = 0x20,
    BLOCKBYTES = 0x40
  };

  struct SHA256Context {
    uint64 Bytes;
    uint32 Key[BLOCKWORDS];
    uint32 Iv[HASHWORDS];
  };
  SHA256Hash() { Init(); }
  ~SHA256Hash() {}

  static bool Compute(const void *datain, uint32 size, void* hash, uint32 hashsize);
  void Init();
  void Update(const void *input, uint32 len);
  void Final(BYTE hash[HASHBYTES]);
  static bool Test();
  static bool GetStr(const wchar_t* wzsIn, char* data, int count);
  static bool GetStr(const wchar_t* wszIn, wchar_t* data, int count);

private:
  SHA256Context SHA256;
  const static uint32 K[64];

  static void SwapBuffer32(void *dest, const void *src, uint32 words);
  static void Sha256Init(void *priv);
  static void Sha256Transform(uint32 *block, uint32 *key);
  static void Sha256Update(void *priv, void const *bufIn, uint32 len);
  static void const * Sha256Final(void *priv);
  static void ComputeSHAInRounds(BYTE sha[HASHBYTES], uint32 rounds);
};

#endif
#endif