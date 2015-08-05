#include "stdafx.h"
#include "Hashing.h"
#include "Helper.h"

bool MD5Hash::Test() {
  BYTE md5[HASHBYTES];
  ComputeMD5InRounds(md5, 0x100);
  const uint32 *x = reinterpret_cast<const uint32*>(md5);
  return x[0] == 0xD072076F && x[1] == 0x74F2EF9D && x[2] == 0x9A652110 && x[3] == 0xBCFA6E73;
}

bool SHA256Hash::Test() {
  BYTE sha[HASHBYTES];
  ComputeSHAInRounds(sha, 0x100);
  const uint64 *x = reinterpret_cast<const uint64*>(sha);
  return x[0] == 0x5A8CB9CA2846C919 && x[1] == 0xC38D0720E6E8147F && x[2] == 0x6AE1C92C5B38D369 && x[3] == 0x053263C0BDEFFBDC;
}

#ifdef _USE_IPP
MD5Hash::MD5Hash() : Context(0) {
  Init();
}

MD5Hash::~MD5Hash() {
  CloseContext();
}

void MD5Hash::CloseContext() {
  if (Context) {
    ippFree(Context);
    Context = 0;
  }
}

/*bool MD5Hash::Compute(const void *datain, int size, void* hash, int hashsize) {
  IppStatus err = ippStsErr;
  if (Context) {
    err = ippsMD5Update(reinterpret_cast<const Ipp8u*>(datain), size, reinterpret_cast<IppsMD5State *>(Context));
    if (ippStsNoErr == err) {
      if (hashsize >= HASHBYTES)
        err = ippsMD5Final(reinterpret_cast<Ipp8u*>(hash), reinterpret_cast<IppsMD5State *>(Context));
      else
        err = ippStsErr;
    }
  }
  return ippStsNoErr == err;
}*/

bool MD5Hash::Compute(const void *datain, int size, void* hash, int hashsize) {
  MD5Hash md5;
  if (hashsize >= HASHBYTES) {
    md5.Init();
    md5.Update(datain, size);
    md5.Final(hash, HASHBYTES);
    return true;
  }
  return false;
}

bool MD5Hash::Update(const void *datain, int size) {
  IppStatus err = ippStsErr;
  if (Context)
    err = ippsMD5Update(reinterpret_cast<const Ipp8u*>(datain), size, reinterpret_cast<IppsMD5State *>(Context));
  return  err == ippStsNoErr;
}

bool MD5Hash::Final(void* hash, int hashsize) {
  IppStatus err = ippStsErr;
  if (Context) {
    if (hashsize >= HASHBYTES)
      err = ippsMD5Final(reinterpret_cast<Ipp8u*>(hash), reinterpret_cast<IppsMD5State *>(Context));
    else
      err = ippStsErr;
  }
  return  ippStsNoErr == err;
}

void MD5Hash::ComputeMD5InRounds(BYTE hash[HASHBYTES], uint32 rounds) {
  BYTE *md5buffer = 0;
  MD5Hash md5;
  if (md5buffer = new BYTE[rounds *HASHBYTES]) {
    for (uint32 i = 0; i < rounds; ++i) {
      MD5Hash::Compute(md5buffer, i, hash, HASHBYTES);
      ::memcpy(&md5buffer[i*HASHBYTES], hash, HASHBYTES);
    }
    MD5Hash::Compute(md5buffer, rounds * HASHBYTES, hash, HASHBYTES);
    delete[] md5buffer;
  }
}


bool MD5Hash::Init() {
  int ctxSize = 0;
  CloseContext();
  IppStatus err = ippsMD5GetSize(&ctxSize);
  IppsMD5State *pCtx = 0;
  if (ippStsNoErr == err) {
    pCtx = reinterpret_cast<IppsMD5State *>(ippMalloc(ctxSize));
    if (pCtx)
      err = ippsMD5Init(pCtx);
    else
      err = ippStsErr;
  }
  else
    err = ippStsErr;
  if (ippStsNoErr == err) {
    Context = pCtx;
    return true;
  }
  else {
    if (pCtx)
      ippFree(pCtx);
    return false;
  }
}

SHA256Hash::SHA256Hash() : Context(0) {
  Init();
}

SHA256Hash::~SHA256Hash() {
  CloseContext();
}

void SHA256Hash::CloseContext() {
  if (Context) {
    ippFree(Context);
    Context = 0;
  }
}

/*bool SHA256Hash::Compute(const void *datain, int size, void* hash, int hashsize){
  IppStatus err = ippStsErr;
  if (Context) {
    err = ippsSHA256Update(reinterpret_cast<const Ipp8u*>(datain), size, reinterpret_cast<IppsSHA256State *>(Context));
    if (ippStsNoErr == err) {
      if (hashsize >= HASHBYTES)
        err = ippsSHA256Final(reinterpret_cast<Ipp8u*>(hash), reinterpret_cast<IppsSHA256State *>(Context));
      else
        err = ippStsErr;
    }
  }
  return ippStsNoErr == err;
}*/

bool SHA256Hash::Compute(const void *datain, int size, void* hash, int hashsize) {
  SHA256Hash sha;
  if (hashsize >= HASHBYTES) {
    sha.Init();
    sha.Update(datain, size);
    sha.Final(hash, HASHBYTES);
    return true;
  }
  return false;
}

bool SHA256Hash::Init() {
  int ctxSize = 0;
  CloseContext();
  IppStatus err = ippsSHA256GetSize(&ctxSize);
  IppsSHA256State *pCtx = 0;
  if (ippStsNoErr == err) {
    pCtx = reinterpret_cast<IppsSHA256State *>(ippMalloc(ctxSize));
    if (pCtx)
      err = ippsSHA256Init(pCtx);
    else
      err = ippStsErr;
  }
  else
    err = ippStsErr;
  if (ippStsNoErr == err) {
    Context = pCtx;
    return true;
  }
  else {
    if (pCtx)
      ippFree(pCtx);
    return false;
  }
}

bool SHA256Hash::Update(const void *datain, int size) {
  IppStatus err = ippStsErr;
  if (Context)
    err = ippsSHA256Update(reinterpret_cast<const Ipp8u*>(datain), size, reinterpret_cast<IppsSHA256State *>(Context));
  return  err == ippStsNoErr;
}

bool SHA256Hash::Final(void* hash, int hashsize) {
  IppStatus err = ippStsErr;
  if (Context) {
    if (hashsize >= HASHBYTES)
      err = ippsSHA256Final(reinterpret_cast<Ipp8u*>(hash), reinterpret_cast<IppsSHA256State *>(Context));
    else
      err = ippStsErr;
  }
  return  ippStsNoErr == err;
}

void SHA256Hash::ComputeSHAInRounds(BYTE hash[HASHBYTES], uint32 rounds) {
  BYTE *shabuffer = 0;
  SHA256Hash sha;
  if (shabuffer = new BYTE[rounds *HASHBYTES]) {
    for (uint32 i = 0; i < rounds; ++i) {
      SHA256Hash::Compute(shabuffer, i, hash, HASHBYTES);
      ::memcpy(&shabuffer[i*HASHBYTES], hash, HASHBYTES);
    }
    SHA256Hash::Compute(shabuffer, rounds * HASHBYTES, hash, HASHBYTES);
    delete[]shabuffer;
  }
}
#else

void MD5Hash::ComputeMD5InRounds(BYTE hash[HASHBYTES], uint32 rounds) {
  BYTE *md5buffer = 0;
  MD5Hash md5;
  if (md5buffer = new BYTE[rounds *HASHBYTES]) {
    for (uint32 i = 0; i < rounds; ++i) {
      md5.Init();
      md5.Update(md5buffer, i);
      md5.Final(hash);
      ::memcpy(&md5buffer[i*HASHBYTES], hash, HASHBYTES);
    }
    Compute(md5buffer, rounds * HASHBYTES, hash, HASHBYTES);
    delete[] md5buffer;
  }
}

MD5Hash::MD5Hash() {
  Init();
}

void MD5Hash::Init() {
  State[3] = 0x10325476UL;
  State[0] = 0x67452301UL;
  State[2] = 0x98BADCFEUL;
  State[1] = 0xEFCDAB89UL;

  Count[0] = 0;
  Count[1] = 0;
}

void MD5Hash::Update(const void *input, uint32 len) {
  uint32 index = (uint32)((Count[0] >> 3) & BLOCKMASK);
  uint32 currentlen = static_cast<uint32>(len) << 3;
  Count[0] += currentlen;
  if (Count[0] < currentlen)
    Count[1]++;
  Count[1] += (static_cast<uint32>(len) >> 29);
  uint32 partLen = 64 - index;
  uint32 i;
  if (len >= partLen) {
    memcpy_s(Buffer + index, partLen, input, partLen);
    Perform(Buffer);
    for (i = partLen; i + BLOCKSIZE - 1 < len; i += BLOCKSIZE)
      Perform(&reinterpret_cast<const BYTE*>(input)[i]);
    index = 0;
  }
  else
    i = 0;
  len -= i;
  if (len)
    ::memcpy_s(&Buffer[index], len, &reinterpret_cast<const BYTE*>(input)[i], len);
}

void MD5Hash::Final(BYTE hash[HASHBYTES]) {
  BYTE bits[2 * sizeof(uint32)];
  BYTE padding[BLOCKSIZE];
  ::memcpy_s(bits, sizeof(bits), Count, sizeof(bits));
  ::memset(padding, 0, BLOCKSIZE);
  uint32 index = (uint32)((Count[0] >> 3) & 0x3F);
  uint32 padLen = (index < 56) ? (56 - index) : (120 - index);
  *padding = 0x80U;
  Update(padding, padLen);
  Update(bits, sizeof(bits));
  ::memcpy_s(hash, HASHBYTES, State, sizeof(State));
}

void MD5Hash::Perform(const BYTE block[BLOCKSIZE]) {
  uint32 a = State[0];
  uint32 b = State[1];
  uint32 c = State[2];
  uint32 d = State[3];
  uint32 x[HASHBYTES];

  ::memcpy_s(x, BLOCKSIZE, block, BLOCKSIZE);

  FUNC(F, a, b, c, d, x[0], 7, 0xD76AA478UL);
  FUNC(F, d, a, b, c, x[1], 12, 0xE8C7B756UL);
  FUNC(F, c, d, a, b, x[2], 17, 0x242070DBUL);
  FUNC(F, b, c, d, a, x[3], 22, 0xC1BDCEEEUL);
  FUNC(F, a, b, c, d, x[4], 7, 0xF57C0FAFUL);
  FUNC(F, d, a, b, c, x[5], 12, 0x4787C62AUL);
  FUNC(F, c, d, a, b, x[6], 17, 0xA8304613UL);
  FUNC(F, b, c, d, a, x[7], 22, 0xFD469501UL);
  FUNC(F, a, b, c, d, x[8], 7, 0x698098D8UL);
  FUNC(F, d, a, b, c, x[9], 12, 0x8B44F7AFUL);
  FUNC(F, c, d, a, b, x[10], 17, 0xFFFF5BB1UL);
  FUNC(F, b, c, d, a, x[11], 22, 0x895CD7BEUL);
  FUNC(F, a, b, c, d, x[12], 7, 0x6B901122UL);
  FUNC(F, d, a, b, c, x[13], 12, 0xFD987193UL);
  FUNC(F, c, d, a, b, x[14], 17, 0xA679438EUL);
  FUNC(F, b, c, d, a, x[15], 22, 0x49B40821UL);

  FUNC(G, a, b, c, d, x[1], 5, 0xF61E2562UL);
  FUNC(G, d, a, b, c, x[6], 9, 0xC040B340UL);
  FUNC(G, c, d, a, b, x[11], 14, 0x265E5A51UL);
  FUNC(G, b, c, d, a, x[0], 20, 0xE9B6C7AAUL);
  FUNC(G, a, b, c, d, x[5], 5, 0xD62F105DUL);
  FUNC(G, d, a, b, c, x[10], 9, 0x02441453UL);
  FUNC(G, c, d, a, b, x[15], 14, 0xD8A1E681UL);
  FUNC(G, b, c, d, a, x[4], 20, 0xE7D3FBC8UL);
  FUNC(G, a, b, c, d, x[9], 5, 0x21E1CDE6UL);
  FUNC(G, d, a, b, c, x[14], 9, 0xC33707D6UL);
  FUNC(G, c, d, a, b, x[3], 14, 0xF4D50D87UL);
  FUNC(G, b, c, d, a, x[8], 20, 0x455A14EDUL);
  FUNC(G, a, b, c, d, x[13], 5, 0xA9E3E905UL);
  FUNC(G, d, a, b, c, x[2], 9, 0xFCEFA3F8UL);
  FUNC(G, c, d, a, b, x[7], 14, 0x676F02D9UL);
  FUNC(G, b, c, d, a, x[12], 20, 0x8D2A4C8AUL);

  FUNC(H, a, b, c, d, x[5], 4, 0xFFFA3942UL);
  FUNC(H, d, a, b, c, x[8], 11, 0x8771F681UL);
  FUNC(H, c, d, a, b, x[11], 16, 0x6D9D6122UL);
  FUNC(H, b, c, d, a, x[14], 23, 0xFDE5380CUL);
  FUNC(H, a, b, c, d, x[1], 4, 0xA4BEEA44UL);
  FUNC(H, d, a, b, c, x[4], 11, 0x4BDECFA9UL);
  FUNC(H, c, d, a, b, x[7], 16, 0xF6BB4B60UL);
  FUNC(H, b, c, d, a, x[10], 23, 0xBEBFBC70UL);
  FUNC(H, a, b, c, d, x[13], 4, 0x289B7EC6UL);
  FUNC(H, d, a, b, c, x[0], 11, 0xEAA127FAUL);
  FUNC(H, c, d, a, b, x[3], 16, 0xD4EF3085UL);
  FUNC(H, b, c, d, a, x[6], 23, 0x04881D05UL);
  FUNC(H, a, b, c, d, x[9], 4, 0xD9D4D039UL);
  FUNC(H, d, a, b, c, x[12], 11, 0xE6DB99E5UL);
  FUNC(H, c, d, a, b, x[15], 16, 0x1FA27CF8UL);
  FUNC(H, b, c, d, a, x[2], 23, 0xC4AC5665UL);

  FUNC(I, a, b, c, d, x[0], 6, 0xF4292244UL);
  FUNC(I, d, a, b, c, x[7], 10, 0x432AFF97UL);
  FUNC(I, c, d, a, b, x[14], 15, 0xAB9423A7UL);
  FUNC(I, b, c, d, a, x[5], 21, 0xFC93A039UL);
  FUNC(I, a, b, c, d, x[12], 6, 0x655B59C3UL);
  FUNC(I, d, a, b, c, x[3], 10, 0x8F0CCC92UL);
  FUNC(I, c, d, a, b, x[10], 15, 0xFFEFF47DUL);
  FUNC(I, b, c, d, a, x[1], 21, 0x85845DD1UL);
  FUNC(I, a, b, c, d, x[8], 6, 0x6FA87E4FUL);
  FUNC(I, d, a, b, c, x[15], 10, 0xFE2CE6E0UL);
  FUNC(I, c, d, a, b, x[6], 15, 0xA3014314UL);
  FUNC(I, b, c, d, a, x[13], 21, 0x4E0811A1UL);
  FUNC(I, a, b, c, d, x[4], 6, 0xF7537E82UL);
  FUNC(I, d, a, b, c, x[11], 10, 0xBD3AF235UL);
  FUNC(I, c, d, a, b, x[2], 15, 0x2AD7D2BBUL);
  FUNC(I, b, c, d, a, x[9], 21, 0xEB86D391UL);

  State[3] += d;
  State[0] += a;
  State[2] += c;
  State[1] += b;
}

bool MD5Hash::Compute(const void *datain, uint32 size, void* hash, uint32 hashsize) {
  if (hash && hashsize >= HASHBYTES) {
    MD5Hash md5;
    md5.Update(datain, size);
    md5.Final(reinterpret_cast<BYTE*>(hash));
    return true;
  }
  return false;
}

//SHA256========================================================================
const uint32 SHA256Hash::K[64] = {
  0x428A2F98, 0x71374491, 0xB5C0FBCF, 0xE9B5DBA5,
  0x3956C25B, 0x59F111F1, 0x923F82A4, 0xAB1C5ED5,
  0xD807AA98, 0x12835B01, 0x243185BE, 0x550C7DC3,
  0x72BE5D74, 0x80DEB1FE, 0x9BDC06A7, 0xC19BF174,
  0xE49B69C1, 0xEFBE4786, 0x0FC19DC6, 0x240CA1CC,
  0x2DE92C6F, 0x4A7484AA, 0x5CB0A9DC, 0x76F988DA,
  0x983E5152, 0xA831C66D, 0xB00327C8, 0xBF597FC7,
  0xC6E00BF3, 0xD5A79147, 0x06CA6351, 0x14292967,
  0x27B70A85, 0x2E1B2138, 0x4D2C6DFC, 0x53380D13,
  0x650A7354, 0x766A0ABB, 0x81C2C92E, 0x92722C85,
  0xA2BFE8A1, 0xA81A664B, 0xC24B8B70, 0xC76C51A3,
  0xD192E819, 0xD6990624, 0xF40E3585, 0x106AA070,
  0x19A4C116, 0x1E376C08, 0x2748774C, 0x34B0BCB5,
  0x391C0CB3, 0x4ED8AA4A, 0x5B9CCA4F, 0x682E6FF3,
  0x748F82EE, 0x78A5636F, 0x84C87814, 0x8CC70208,
  0x90BEFFFA, 0xA4506CEB, 0xBEF9A3F7, 0xC67178F2
};

bool SHA256Hash::Compute(const void *datain, uint32 size, void* hash, uint32 hashsize) {
  if (hash && hashsize >= HASHBYTES) {
    SHA256Hash sha;
    sha.Update(datain, size);
    sha.Final(reinterpret_cast<BYTE*>(hash));
    return true;
  }
  return false;
}

void SHA256Hash::ComputeSHAInRounds(BYTE sha[HASHBYTES], uint32 rounds) {
  BYTE *shabuffer = 0;
  SHA256Hash sha256;
  if (shabuffer = new BYTE[rounds *HASHBYTES]) {
    for (uint32 i = 0; i < rounds; ++i) {
      sha256.Init();
      sha256.Update(shabuffer, i);
      sha256.Final(sha);
      ::memcpy(&shabuffer[i*HASHBYTES], sha, HASHBYTES);
    }
    Compute(shabuffer, rounds * HASHBYTES, sha, HASHBYTES);
    delete[] shabuffer;
  }
}

void SHA256Hash::Init() {
  Sha256Init(&SHA256);
}

void SHA256Hash::Update(const void *input, uint32 len) {
  Sha256Update(&SHA256, input, len);
}

void SHA256Hash::Final(BYTE hash[HASHBYTES]) {
  ::memcpy(hash, Sha256Final(&SHA256), HASHBYTES);
}

void SHA256Hash::SwapBuffer32(void *dest, const void *src, uint32 words) {
  const uint32 *s = reinterpret_cast<const uint32*>(src);
  uint32       *d = reinterpret_cast<uint32*>(dest);
  while (words--)
    *d++ = _byteswap_ulong(*s++);
}

void SHA256Hash::Sha256Init(void *priv) {
  SHA256Context *ctx = reinterpret_cast<SHA256Context*>(priv);
  ctx->Iv[0] = 0x6A09E667;
  ctx->Iv[1] = 0xBB67AE85;
  ctx->Iv[2] = 0x3C6EF372;
  ctx->Iv[3] = 0xA54FF53A;
  ctx->Iv[4] = 0x510E527F;
  ctx->Iv[5] = 0x9B05688C;
  ctx->Iv[6] = 0x1F83D9AB;
  ctx->Iv[7] = 0x5BE0CD19;
  ctx->Bytes = 0;
}

void SHA256Hash::Sha256Transform(uint32 *block, uint32 *key) {
  register uint32 A, B, C, D, E, F, G, H;

  /* Set up first buffer */
  A = block[0];
  B = block[1];
  C = block[2];
  D = block[3];
  E = block[4];
  F = block[5];
  G = block[6];
  H = block[7];

  subRound256(A, B, C, D, E, F, G, H, K[0], key[0]);
  subRound256(H, A, B, C, D, E, F, G, K[1], key[1]);
  subRound256(G, H, A, B, C, D, E, F, K[2], key[2]);
  subRound256(F, G, H, A, B, C, D, E, K[3], key[3]);
  subRound256(E, F, G, H, A, B, C, D, K[4], key[4]);
  subRound256(D, E, F, G, H, A, B, C, K[5], key[5]);
  subRound256(C, D, E, F, G, H, A, B, K[6], key[6]);
  subRound256(B, C, D, E, F, G, H, A, K[7], key[7]);

  subRound256(A, B, C, D, E, F, G, H, K[8], key[8]);
  subRound256(H, A, B, C, D, E, F, G, K[9], key[9]);
  subRound256(G, H, A, B, C, D, E, F, K[10], key[10]);
  subRound256(F, G, H, A, B, C, D, E, K[11], key[11]);
  subRound256(E, F, G, H, A, B, C, D, K[12], key[12]);
  subRound256(D, E, F, G, H, A, B, C, K[13], key[13]);
  subRound256(C, D, E, F, G, H, A, B, K[14], key[14]);
  subRound256(B, C, D, E, F, G, H, A, K[15], key[15]);

  subRound256(A, B, C, D, E, F, G, H, K[16], expand256(key, 16));
  subRound256(H, A, B, C, D, E, F, G, K[17], expand256(key, 17));
  subRound256(G, H, A, B, C, D, E, F, K[18], expand256(key, 18));
  subRound256(F, G, H, A, B, C, D, E, K[19], expand256(key, 19));
  subRound256(E, F, G, H, A, B, C, D, K[20], expand256(key, 20));
  subRound256(D, E, F, G, H, A, B, C, K[21], expand256(key, 21));
  subRound256(C, D, E, F, G, H, A, B, K[22], expand256(key, 22));
  subRound256(B, C, D, E, F, G, H, A, K[23], expand256(key, 23));

  subRound256(A, B, C, D, E, F, G, H, K[24], expand256(key, 24));
  subRound256(H, A, B, C, D, E, F, G, K[25], expand256(key, 25));
  subRound256(G, H, A, B, C, D, E, F, K[26], expand256(key, 26));
  subRound256(F, G, H, A, B, C, D, E, K[27], expand256(key, 27));
  subRound256(E, F, G, H, A, B, C, D, K[28], expand256(key, 28));
  subRound256(D, E, F, G, H, A, B, C, K[29], expand256(key, 29));
  subRound256(C, D, E, F, G, H, A, B, K[30], expand256(key, 30));
  subRound256(B, C, D, E, F, G, H, A, K[31], expand256(key, 31));

  subRound256(A, B, C, D, E, F, G, H, K[32], expand256(key, 32));
  subRound256(H, A, B, C, D, E, F, G, K[33], expand256(key, 33));
  subRound256(G, H, A, B, C, D, E, F, K[34], expand256(key, 34));
  subRound256(F, G, H, A, B, C, D, E, K[35], expand256(key, 35));
  subRound256(E, F, G, H, A, B, C, D, K[36], expand256(key, 36));
  subRound256(D, E, F, G, H, A, B, C, K[37], expand256(key, 37));
  subRound256(C, D, E, F, G, H, A, B, K[38], expand256(key, 38));
  subRound256(B, C, D, E, F, G, H, A, K[39], expand256(key, 39));

  subRound256(A, B, C, D, E, F, G, H, K[40], expand256(key, 40));
  subRound256(H, A, B, C, D, E, F, G, K[41], expand256(key, 41));
  subRound256(G, H, A, B, C, D, E, F, K[42], expand256(key, 42));
  subRound256(F, G, H, A, B, C, D, E, K[43], expand256(key, 43));
  subRound256(E, F, G, H, A, B, C, D, K[44], expand256(key, 44));
  subRound256(D, E, F, G, H, A, B, C, K[45], expand256(key, 45));
  subRound256(C, D, E, F, G, H, A, B, K[46], expand256(key, 46));
  subRound256(B, C, D, E, F, G, H, A, K[47], expand256(key, 47));

  subRound256(A, B, C, D, E, F, G, H, K[48], expand256(key, 48));
  subRound256(H, A, B, C, D, E, F, G, K[49], expand256(key, 49));
  subRound256(G, H, A, B, C, D, E, F, K[50], expand256(key, 50));
  subRound256(F, G, H, A, B, C, D, E, K[51], expand256(key, 51));
  subRound256(E, F, G, H, A, B, C, D, K[52], expand256(key, 52));
  subRound256(D, E, F, G, H, A, B, C, K[53], expand256(key, 53));
  subRound256(C, D, E, F, G, H, A, B, K[54], expand256(key, 54));
  subRound256(B, C, D, E, F, G, H, A, K[55], expand256(key, 55));

  subRound256(A, B, C, D, E, F, G, H, K[56], expand256(key, 56));
  subRound256(H, A, B, C, D, E, F, G, K[57], expand256(key, 57));
  subRound256(G, H, A, B, C, D, E, F, K[58], expand256(key, 58));
  subRound256(F, G, H, A, B, C, D, E, K[59], expand256(key, 59));
  subRound256(E, F, G, H, A, B, C, D, K[60], expand256(key, 60));
  subRound256(D, E, F, G, H, A, B, C, K[61], expand256(key, 61));
  subRound256(C, D, E, F, G, H, A, B, K[62], expand256x(key, 62));
  subRound256(B, C, D, E, F, G, H, A, K[63], expand256x(key, 63));

  block[0] += A;
  block[1] += B;
  block[2] += C;
  block[3] += D;
  block[4] += E;
  block[5] += F;
  block[6] += G;
  block[7] += H;
}

void SHA256Hash::Sha256Update(void *priv, void const *bufIn, uint32 len) {
  SHA256Context *ctx = reinterpret_cast<SHA256Context*>(priv);
  byte const    *buf = reinterpret_cast<byte const*>(bufIn);
  uint32          i = (uint32)(ctx->Bytes & ALL_BITS_32);
  i %= BLOCKBYTES;
  ctx->Bytes += len;
  if (BLOCKBYTES - i > len)
    ::memcpy((byte *)ctx->Key + i, buf, len);
  else {
    if (i) {
      ::memcpy((byte *)ctx->Key + i, buf, BLOCKBYTES - i);
      SwapBuffer32(ctx->Key, ctx->Key, BLOCKWORDS);
      Sha256Transform(ctx->Iv, ctx->Key);
      buf += BLOCKBYTES - i;
      len -= BLOCKBYTES - i;
    }
    while (len >= BLOCKBYTES) {
      SwapBuffer32(ctx->Key, buf, BLOCKWORDS);
      Sha256Transform(ctx->Iv, ctx->Key);
      buf += BLOCKBYTES;
      len -= BLOCKBYTES;
    }
    if (len)
      ::memcpy(ctx->Key, buf, len);
  }
}

void const *SHA256Hash::Sha256Final(void *priv) {
  SHA256Context *ctx = reinterpret_cast<SHA256Context*>(priv);
  uint32           i = (uint32)(ctx->Bytes & ALL_BITS_32);
  i %= BLOCKBYTES;
  SwapBuffer32(ctx->Key, ctx->Key, (i + 3) >> 2);
  ctx->Key[i >> 2] &= 0xffffff80 << 8 * (~i & 3);
  ctx->Key[i >> 2] |= 0x00000080 << 8 * (~i & 3);
  if (i > BLOCKBYTES - 9) {
    if (i < 60)
      ctx->Key[15] = 0;
    Sha256Transform(ctx->Iv, ctx->Key);
    i = 0;
  }
  else
    i = (i >> 2) + 1;
  ::memset(ctx->Key + i, 0, (14 - i)  * sizeof(uint32));
  ctx->Key[14] = (uint32)((ctx->Bytes >> 29) & ALL_BITS_32);
  ctx->Key[15] = static_cast<uint32>(ctx->Bytes << 3);
  Sha256Transform(ctx->Iv, ctx->Key);
  SwapBuffer32(ctx->Iv, ctx->Iv, HASHWORDS);
  return reinterpret_cast<byte const*>(ctx->Iv);
}
#endif

bool MD5Hash::GetStr(const wchar_t* wszIn, char* data, int count) {
  bool ret = false;
  int needSize = 2 * HASHBYTES + 1;
  if (count < needSize)
    return false;
  unsigned char hash[HASHBYTES];
  size_t charcount = wcslen(wszIn) + 1;
  wchar_t *wszUpperIn = new wchar_t[charcount];
  if (wszUpperIn) {
    if (SUCCEEDED(StringCchCopy(wszUpperIn, charcount, wszIn))) {
      ToUpper(wszUpperIn);
      MD5Hash::Compute(wszUpperIn, static_cast<int>(wcslen(wszUpperIn) * 2), hash, sizeof(hash));
      BinToHex(hash, sizeof(hash), data);
      ret = true;
    }
    delete[] wszUpperIn;
  }
  return ret;
}

bool MD5Hash::GetStr(const wchar_t* wszIn, wchar_t* data, int count) {
  bool ret = false;
  int needSize = 2 * HASHBYTES + 1;
  if (count < needSize)
    return false;
  unsigned char hash[HASHBYTES];
  size_t charcount = wcslen(wszIn) + 1;
  wchar_t *wszUpperIn = new wchar_t[charcount];
  if (wszUpperIn) {
    if (SUCCEEDED(StringCchCopy(wszUpperIn, charcount, wszIn))) {
      ToUpper(wszUpperIn);
      MD5Hash::Compute(wszUpperIn, static_cast<int>(wcslen(wszUpperIn) * 2), hash, sizeof(hash));
      BinToHex(hash, sizeof(hash), data);
      ret = true;
    }
    delete[] wszUpperIn;
  }
  return ret;
}

bool SHA256Hash::GetStr(const wchar_t* wszIn, char* data, int count) {
  bool ret = false;
  int needSize = 2 * HASHBYTES + 1;
  if (count < needSize)
    return false;
  unsigned char hash[HASHBYTES];
  size_t charcount = wcslen(wszIn) + 1;
  wchar_t *wszUpperIn = new wchar_t[charcount];
  if (wszUpperIn) {
    if (SUCCEEDED(StringCchCopy(wszUpperIn, charcount, wszIn))) {
      ToUpper(wszUpperIn);
      SHA256Hash::Compute(wszUpperIn, static_cast<int>(wcslen(wszUpperIn) * 2), hash, sizeof(hash));
      BinToHex(hash, sizeof(hash), data);
      ret = true;
    }
    delete[] wszUpperIn;
  }
  return ret;
}

bool SHA256Hash::GetStr(const wchar_t* wszIn, wchar_t* data, int count) {
  bool ret = false;
  int needSize = 2 * HASHBYTES + 1;
  if (count < needSize)
    return false;
  unsigned char hash[HASHBYTES];
  size_t charcount = wcslen(wszIn) + 1;
  wchar_t *wszUpperIn = new wchar_t[charcount];
  if (wszUpperIn) {
    if (SUCCEEDED(StringCchCopy(wszUpperIn, charcount, wszIn))) {
      ToUpper(wszUpperIn);
      SHA256Hash::Compute(wszUpperIn, static_cast<int>(wcslen(wszUpperIn) * 2), hash, sizeof(hash));
      BinToHex(hash, sizeof(hash), data);
      ret = true;
    }
    delete[] wszUpperIn;
  }
  return ret;
}