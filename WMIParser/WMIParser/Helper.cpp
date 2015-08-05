#include "stdafx.h"
#include "Helper.h"
#include "Hashing.h"


static char HexDigitA[]  = { '0', '1', '2', '3', '4', '5', '6', '7', '8', '9', 'A', 'B', 'C', 'D', 'E', 'F' };
static char HexDigitW[] = { L'0', L'1', L'2', L'3', L'4', L'5', L'6', L'7', L'8', L'9', L'A', L'B', L'C', L'D', L'E', L'F' };

void BinToHex(unsigned char *hash, int size, char *szHash) {
  char *cur = szHash;
  for (int i = 0; i < size; i++)
  {
    *(cur++) = HexDigitA[hash[i] >> 4];
    *(cur++) = HexDigitA[hash[i] & 0xF];
  }
  *cur = 0;
}

void BinToHex(unsigned char *hash, int size, wchar_t *wszHash) {
  wchar_t *cur = wszHash;
  for (int i = 0; i < size; i++)
  {
    *(cur++) = HexDigitW[hash[i] >> 4];
    *(cur++) = HexDigitW[hash[i] & 0xF];
  }
  *cur = 0;
}

void ToUpper(wchar_t *wszIn) {
  while (*wszIn) {
    *wszIn = toupper(*wszIn);
    ++wszIn;
  }
}

int CompareStringIDFunc(const void *s1, const void *s2) {
  const char *str1 = reinterpret_cast<const char *>(s1);
  const char *str2 = reinterpret_cast<const char *>(s2);
  return _stricmp(str1, str2);
}

FILE * CreateLogFile(const wchar_t* outlog, const wchar_t* perm) {
  FILE* pOutFile = 0;
  if (outlog && *outlog && perm && *perm) {
    if (errno_t err = ::_wfopen_s(&pOutFile, outlog, perm)) {
      wprintf(L"CreateLogFile - _wfopen_s failed = 0x%X\r\n", err);
      pOutFile = 0;
    }
  }
  //else
    //wprintf(L"CreateLogFile - input validation failed.\r\n");
  return pOutFile;
}

void PrintBuffer(const void *buffer, unsigned int size, FILE* out) {
  const unsigned char * bytes = reinterpret_cast<const unsigned char*>(buffer);
  if (bytes) {
    unsigned int blocks = size / 0x10,
      reminder = size % 0x10;
    for (unsigned int i = 0; i < blocks; ++i)
      MyPrintFunc(out, L"0x%.2X 0x%.2X 0x%.2X 0x%.2X 0x%.2X 0x%.2X 0x%.2X 0x%.2X 0x%.2X 0x%.2X 0x%.2X 0x%.2X 0x%.2X 0x%.2X 0x%.2X 0x%.2X\r\n",
      bytes[i * 0x10], bytes[i * 0x10 + 1], bytes[i * 0x10 + 2], bytes[i * 0x10 + 3], bytes[i * 0x10 + 4], bytes[i * 0x10 + 5], bytes[i * 0x10 + 6], bytes[i * 0x10 + 7],
      bytes[i * 0x10 + 8], bytes[i * 0x10 + 9], bytes[i * 0x10 + 10], bytes[i * 0x10 + 11], bytes[i * 0x10 + 12], bytes[i * 0x10 + 13], bytes[i * 0x10 + 14], bytes[i * 0x10 + 15]);

    if (reminder) {
      for (unsigned int i = 0; i < reminder; ++i)
        MyPrintFunc(out, L"0x%.2X ", bytes[blocks * 0x10 + i]);
      MyPrintFunc(out, L"\r\n");
    }

  }
}

void MyPrintFunc(FILE* pOutFile, const wchar_t *format, ...) {
  try {
    va_list args;
    va_start(args, format);
    if (pOutFile)
      vfwprintf_s(pOutFile, format, args);
    else
      vwprintf_s(format, args);
    va_end(args);
  } 
  catch (...) {
    wprintf(L"MyPrintFunc exception.\r\n");
  }
}

int GetTocSize(const ConsumerDataType* data, int count, int init) {
  int size = init;
  const ConsumerDataType* enddata = data + count;
  while (data < enddata) {
    size += data->Size;
    data++;
  }
  return size;
}

HANDLE InitObjFile(const wchar_t *path) {
  _TCHAR wszObjFile[MAX_PATH];
  HANDLE hFile = INVALID_HANDLE_VALUE;
  int len = _snwprintf_s(wszObjFile, MAX_PATH, _TRUNCATE, L"%s\\Objects.data", path);
  if (len && len < MAX_PATH)
    hFile = ::CreateFile(wszObjFile, GENERIC_READ, FILE_SHARE_READ, NULL, OPEN_EXISTING, FILE_ATTRIBUTE_NORMAL, NULL);
  return hFile;
}

void GetStrId(std::string &strID, std::wstring &strName, bool bXP) {
  char    strHash[MAX_STRING_WIN7_COUNT + 1];
  if (bXP)
    MD5Hash::GetStr(strName.c_str(), strHash, sizeof(strHash));
  else
    SHA256Hash::GetStr(strName.c_str(), strHash, sizeof(strHash));
  strID = strHash;
}

void GetWStrId(std::wstring &strID, std::wstring &strName, bool bXP) {
  wchar_t strHash[MAX_STRING_WIN7_COUNT + 1];
  if (bXP)
    MD5Hash::GetStr(strName.c_str(), strHash, sizeof(strHash));
  else
    SHA256Hash::GetStr(strName.c_str(), strHash, sizeof(strHash));
  strID = strHash;
}

void StringArrayValue::Print(HANDLE hFile, FILE *out) {
  if (ValueType == VT_SET) {
    std::vector<StringValue>::iterator it = Values.begin();
    for (; it != Values.end(); ++it)
      it->Print(hFile, out);
  }
  else
    MyPrintFunc(out, L"Not Assigned\r\n");
}

void CreateFieldExtents(uint64 recoffset, uint64 recsize, std::vector<ExtentClass>& extents, std::vector<ExtentClass>& recextents) {
  std::vector<ExtentClass>::iterator it = extents.begin();
  ExtentClass e;
  uint64 currentOff = 0;
  recextents.clear();
  for (; it != extents.end() && recsize; ++it) {
    uint64 start = it->GetStart();
    uint64 count = it->GetCount();
    if (currentOff + count > recoffset && recoffset >= currentOff) {
      uint64 absOff = start + recoffset - currentOff;
      uint64 cursize = recsize;
      if (absOff + recsize > start + count)
        cursize = start + count - absOff;
      recsize -= cursize;
      recextents.push_back(ExtentClass(absOff, cursize));
      currentOff += cursize;
      recoffset = currentOff;
    }
    else
      currentOff += count;

  }
}

uint64 GetWholeSize(std::vector<ExtentClass> &ex) {
  std::vector<ExtentClass>::const_iterator it = ex.cbegin();
  uint64 val = 0;
  for (; it != ex.cend(); ++it) {
    val += it->GetCount();
  }
  return val;
}

const void* GetBufferFromExtents(HANDLE hFile, std::vector<ExtentClass> &ex, uint32& size) {
  size = GetWholeSize(ex) & ALL_BITS_32;
  BYTE *data = new BYTE[size];
  if (data) {
    uint32 index = 0;
    std::vector<ExtentClass>::const_iterator it = ex.cbegin();
    for (; it != ex.cend(); ++it) {
      LARGE_INTEGER offset;
      DWORD justread = 0;
      uint32 chunksize = it->GetCount() & ALL_BITS_32;
      offset.QuadPart = it->GetStart();
      if (INVALID_SET_FILE_POINTER != SetFilePointer(hFile, offset.LowPart, &offset.HighPart, FILE_BEGIN)) {
        if (::ReadFile(hFile, data + index, chunksize, &justread, NULL) && chunksize == justread) {
          index += chunksize;
        }
        else
          break;
      }
      else break;
    }
    if (index == size)
      return data;
    delete[] data;
  }
  return 0;
}

bool GetRecordExtents(HANDLE hObjFile, std::vector<DWORD>& allocMap, LocationStruct &ls, std::vector<ExtentClass>& recordExtents) {
  try {
    DWORD dwPhyPage = allocMap.at(ls.LogicalID);
    LARGE_INTEGER offset;
    offset.QuadPart = dwPhyPage;
    offset.QuadPart *= PAGE_SIZE;
    if (INVALID_SET_FILE_POINTER != SetFilePointer(hObjFile, offset.LowPart, &offset.HighPart, FILE_BEGIN)) {
      DWORD justread = 0;
      BYTE page[PAGE_SIZE];
      if (::ReadFile(hObjFile, page, PAGE_SIZE, &justread, NULL) && PAGE_SIZE == justread) {
        const Toc* toc = reinterpret_cast<const Toc*>(page);
        const Toc* foundtoc = 0;
        while (!toc->IsZero()) {
          if (toc->IsValid(PAGE_SIZE)) {
            if (toc->RecordID == ls.RecordID) {
              if (toc->Size != ls.Size)
                wprintf(L"Size Mismatch : toc size = %.8X map size = %.8X\n", toc->Size, ls.Size);
              foundtoc = toc;
              break;
            }
          }
          toc++;
        }
        if (foundtoc) {
          uint64 currentSize = foundtoc->Size;
          DWORD logicalpage = ls.LogicalID;
          DWORD inpageOffset = foundtoc->Offset;
          while (currentSize) {
            uint64 currentChunk = (PAGE_SIZE - inpageOffset);
            if (currentSize < currentChunk)
              currentChunk = currentSize;
            recordExtents.push_back(ExtentClass(offset.QuadPart + inpageOffset, currentChunk));
            currentSize -= currentChunk;
            inpageOffset = 0;
            if (currentSize) {
              try {
                offset.QuadPart = allocMap.at(++logicalpage);
                offset.QuadPart *= PAGE_SIZE;
              }
              catch (const std::out_of_range &oorex) {
                wprintf_s(L"GetRecordExtents - Exception 2 : %S\r\n", oorex.what());
                break;
              }
            }
          }
          return true;
        }
      }
    }
  }
  catch (const std::out_of_range &oorex) {
    wprintf_s(L"GetRecordExtents - Exception : %S\r\n", oorex.what());
  }
  return false;
}


void StringValue::Print(HANDLE hFile, FILE *out) {
  if (ValueType == VT_SET) {
    DWORD bigsize = static_cast<DWORD>(GetWholeSize(Extents) & 0x7FFFFFFF);
    BYTE *buf = new BYTE[bigsize];
    if (buf) {
      std::vector<ExtentClass>::const_iterator it = Extents.cbegin();
      DWORD totalread = 0;
      for (; it != Extents.cend(); ++it) {
        LARGE_INTEGER li;
        li.QuadPart = it->GetStart();
        bool good = false;
        if (INVALID_SET_FILE_POINTER != ::SetFilePointer(hFile, li.LowPart, &li.HighPart, FILE_BEGIN)) {
          DWORD toRead = static_cast<DWORD>(it->GetCount() & 0x7FFFFFFF);
          DWORD read = 0;
          if (::ReadFile(hFile, buf + totalread, toRead, &read, NULL) && toRead == read)
            totalread += read;
          else {
            wprintf_s(L"Unable to read the String at (%I64d, %d)\r\n", li.QuadPart, toRead);
            break;
          }
        }
        else {
          wprintf_s(L"Unable to set file pointer to (%I64d)\r\n", li.QuadPart);
          break;
        }
      }
      bool good = false;
      wchar_t *destString = new wchar_t[totalread + 1];
      if (destString) {
        size_t written = 0;
        if (TS_STRING == Type) {
          good = !::mbstowcs_s(&written, destString, totalread + 1, reinterpret_cast<const char*>(buf), totalread) && written > 0;
        }
        else if (TS_USTRING == Type) {
          written = totalread / sizeof(wchar_t);
          good = !::wcsncpy_s(destString, totalread, reinterpret_cast<const wchar_t*>(buf), written);
        }
        if (good)
          MyPrintFunc(out, L"%ls\r\n", destString);
        else
          wprintf_s(L"Unable to read the Big String\r\n");
        delete[] destString;
      }
      delete[] buf;
    }
    else
      wprintf_s(L"Unable to alloc %d bytes\r\n", bigsize);
  }
  else
    MyPrintFunc(out, L"Not Assigned\r\n");
}

const wchar_t* StringValue::GetUnicodeValue(HANDLE hFile) {
  if (ValueType == VT_SET) {
    DWORD bigsize = static_cast<DWORD>(GetWholeSize(Extents) & 0x7FFFFFFF);
    BYTE *buf = new BYTE[bigsize];
    if (buf) {
      std::vector<ExtentClass>::const_iterator it = Extents.cbegin();
      DWORD totalread = 0;
      for (; it != Extents.cend(); ++it) {
        LARGE_INTEGER li;
        li.QuadPart = it->GetStart();
        bool good = false;
        if (INVALID_SET_FILE_POINTER != ::SetFilePointer(hFile, li.LowPart, &li.HighPart, FILE_BEGIN)) {
          DWORD toRead = static_cast<DWORD>(it->GetCount() & 0x7FFFFFFF);
          DWORD read = 0;
          if (::ReadFile(hFile, buf + totalread, toRead, &read, NULL) && toRead == read)
            totalread += read;
          else {
            wprintf_s(L"Unable to read the String at (%I64d, %d)\r\n", li.QuadPart, toRead);
            break;
          }
        }
        else {
          wprintf_s(L"Unable to set file pointe to (%I64d)\r\n", li.QuadPart);
          break;
        }
      }
      bool good = false;
      wchar_t *destString = new wchar_t[totalread + 1];
      if (destString) {
        size_t written = 0;
        if (TS_STRING == Type) {
          good = !::mbstowcs_s(&written, destString, totalread + 1, reinterpret_cast<const char*>(buf), totalread) && written > 0;
        }
        else if (TS_USTRING == Type) {
          written = totalread / sizeof(wchar_t);
          good = !::wcsncpy_s(destString, totalread, reinterpret_cast<const wchar_t*>(buf), written);
        }
        if (good)
          wprintf_s(L"%ls\r\n", destString);
        else
          wprintf_s(L"Unable to read the Big String\r\n");
        if (good)
          return destString;
        else
          delete[] destString;
      }
      delete[] buf;
    }
    else
      wprintf_s(L"Unable to alloc %d bytes\r\n", bigsize);
  }
  else
    wprintf_s(L"Not Assigned\r\n");
  return 0;
}

const char* StringValue::GetAniValue(HANDLE hFile) {
  if (ValueType == VT_SET) {
    DWORD bigsize = static_cast<DWORD>(GetWholeSize(Extents) & 0x7FFFFFFF);
    BYTE *buf = new BYTE[bigsize];
    if (buf) {
      std::vector<ExtentClass>::const_iterator it = Extents.cbegin();
      DWORD totalread = 0;
      for (; it != Extents.cend(); ++it) {
        LARGE_INTEGER li;
        li.QuadPart = it->GetStart();
        bool good = false;
        if (INVALID_SET_FILE_POINTER != ::SetFilePointer(hFile, li.LowPart, &li.HighPart, FILE_BEGIN)) {
          DWORD toRead = static_cast<DWORD>(it->GetCount() & 0x7FFFFFFF);
          DWORD read = 0;
          if (::ReadFile(hFile, buf + totalread, toRead, &read, NULL) && toRead == read)
            totalread += read;
          else {
            wprintf_s(L"Unable to read the String at (%I64d, %d)\r\n", li.QuadPart, toRead);
            break;
          }
        }
        else {
          wprintf_s(L"Unable to set file pointe to (%I64d)\r\n", li.QuadPart);
          break;
        }
      }
      bool good = false;
      char *destString = new char[totalread + 1];
      if (destString) {
        size_t written = 0;
        if (TS_STRING == Type) {
          good = !::strncpy_s(destString, totalread + 1, reinterpret_cast<const char*>(buf), totalread);
        }
        else if (TS_USTRING == Type) {
          size_t written = 0;
          good = !::wcstombs_s(&written, destString, totalread + 1, reinterpret_cast<const wchar_t*>(buf), totalread / sizeof(wchar_t)) && written > 0;
        }
        if (!good)
          wprintf_s(L"Unable to read the Big String\r\n");
        if (good)
          return destString;
        else
          delete[] destString;
      }
      delete[] buf;
    }
    else
      wprintf_s(L"Unable to alloc %d bytes\r\n", bigsize);
  }
  else
    wprintf_s(L"Not Assigned\r\n");
  return 0;
}

void DateValue::Print(FILE *out) {
  if (ValueType == VT_SET) {
    SYSTEMTIME systime;
    if (FileTimeToSystemTime(&Value, &systime))
      MyPrintFunc(out, L"%.2d/%.2d/%.4d %.2d:%.2d:%.2d\r\n", systime.wMonth, systime.wDay, systime.wYear, systime.wHour, systime.wMinute, systime.wSecond);
    else
      wprintf_s(L"Unable to print the date.\r\n");
  }
  else
    MyPrintFunc(out, L"Not Assigned\r\n");
}

void Uint64Value::Print(FILE *out) {
  if (ValueType == VT_SET) {
    MyPrintFunc(out, L"%I64u\r\n", Value);
  }
  else
    MyPrintFunc(out, L"Not Assigned\r\n");
}

void Uint32Value::Print(FILE *out) {
  if (ValueType == VT_SET) {
    MyPrintFunc(out, L"%u\r\n", Value);
  }
  else
    MyPrintFunc(out, L"Not Assigned\r\n");
}

void Uint16Value::Print(FILE* out) {
  if (ValueType == VT_SET) {
    MyPrintFunc(out, L"%u\r\n", Value);
  }
  else
    MyPrintFunc(out, L"Not Assigned\r\n");
}

void Sint32Value::Print(FILE* out) {
  if (ValueType == VT_SET) {
    MyPrintFunc(out, L"%d\r\n", Value);
  }
  else
    MyPrintFunc(out, L"Not Assigned\r\n");
}

void BoolValue::Print(FILE* out) {
  if (ValueType == VT_SET) {
    MyPrintFunc(out, L"%ls\r\n", Value ? L"True" : L"False");
  }
  else
    MyPrintFunc(out, L"Not Assigned\r\n");
}

void ByteArrayValue::Print(HANDLE hFile, FILE* out) {
  if (ValueType == VT_SET) {
    std::vector<ExtentClass>::const_iterator it = Extents.cbegin();
    DWORD bigsize = static_cast<DWORD>(GetWholeSize(Extents) & 0x7FFFFFFF);
    DWORD totalread = 0;
    for (; it != Extents.cend(); ++it) {
      LARGE_INTEGER li;
      li.QuadPart = it->GetStart();
      bool good = false;
      if (INVALID_SET_FILE_POINTER != ::SetFilePointer(hFile, li.LowPart, &li.HighPart, FILE_BEGIN)) {
        DWORD toRead = static_cast<DWORD>(it->GetCount() & 0x7FFFFFFF);
        DWORD read = 0;
        byte *buf = new byte[toRead];
        if (buf) {
          if (::ReadFile(hFile, buf, toRead, &read, NULL) && toRead == read) {
            MyPrintFunc(out, L"\r\n");
            PrintBuffer(buf, read, out);
            totalread += read;
            good = true;
          }
          delete[] buf;
        }
      }
      if (!good) {
        wprintf_s(L"Unable to read the byte array at (%I64d, %I64d)\r\n", li.QuadPart, it->GetCount());
        break;
      }
    }
    if (bigsize != totalread)
      wprintf_s(L"Unable to read the whole binary buffer; read 0x%.8X of 0x%.8X.\r\n", totalread, bigsize);
  }
  else
    MyPrintFunc(out, L"Not Assigned\r\n");
}

void SidValue::Print(HANDLE hFile, FILE* out) {
  if (ValueType == VT_SET) {
    DWORD bigsize = static_cast<DWORD>(GetWholeSize(Extents) & 0x7FFFFFFF);
    std::vector<ExtentClass>::const_iterator it = Extents.cbegin();
    DWORD totalread = 0;
    LARGE_INTEGER li;
    for (; it != Extents.cend(); ++it) {
      li.QuadPart = it->GetStart();
      bool good = false;
      if (INVALID_SET_FILE_POINTER != ::SetFilePointer(hFile, li.LowPart, &li.HighPart, FILE_BEGIN)) {
        DWORD toRead = static_cast<DWORD>(it->GetCount() & 0x7FFFFFFF);
        DWORD  read = 0;
        BYTE *buf = new BYTE[toRead];
        if (buf) {
          if (::ReadFile(hFile, buf, toRead, &read, NULL) && toRead == read) {
            //TO DO
            MyPrintFunc(out, L"\r\n");
            PrintBuffer(buf, read, out);
            totalread += read;
            good = true;
          }
          delete[] buf;
        }
      }
      if (!good) {
        wprintf_s(L"Unable to read the SID at (%I64d, %I64d)\r\n", it->GetStart(), it->GetCount());
        break;
      }
    }
    if (bigsize != totalread)
      wprintf_s(L"Unable to read the whole SID; read 0x%.8X of 0x%.8X.\r\n", totalread, bigsize);
  }
  else
    MyPrintFunc(out, L"Not Assigned\r\n");
}

ObjectHeaderClass::ObjectHeaderClass() :
KnownGuid(),
Date1(),
Date2()
{}

ObjectHeaderClass::ObjectHeaderClass(const ObjectHeaderClass &copyin) :
KnownGuid(copyin.KnownGuid),
Date1(copyin.Date1),
Date2(copyin.Date2)
{}

ObjectHeaderClass::~ObjectHeaderClass() {

}

void ObjectHeaderClass::SetKnownGUID(uint64 s, uint64 c, int type) {
  KnownGuid.Set(s, c, type);
}

void ObjectHeaderClass::SetKnownGUID(std::vector<ExtentClass>& extents, int type) {
  if (extents.size() == 1) {
    try {
      KnownGuid.Set(extents.at(0).GetStart(), extents.at(0).GetCount(), type);
    }
    catch (const std::out_of_range &oor) {
      wprintf_s(L"SetKnownGUID - Exception : %S\r\n", oor.what());
    }
  }
  else
    KnownGuid.Set(extents, type);
}

void ObjectHeaderClass::SetDate1(uint64 filetime) {
  Date1 = filetime;
}

void ObjectHeaderClass::SetDate2(uint64 filetime) {
  Date2 = filetime;
}

ObjectHeaderClass& ObjectHeaderClass::operator=(const ObjectHeaderClass &rhs)
{
  this->KnownGuid = rhs.KnownGuid;
  this->Date1 = rhs.Date1;
  this->Date2 = rhs.Date2;

  return *this;
}

bool ObjectHeaderClass::operator==(const ObjectHeaderClass &rhs) const
{
  if (!(this->KnownGuid == rhs.KnownGuid)) return false;
  if (!(this->Date1 == rhs.Date1)) return false;
  if (!(this->Date2 == rhs.Date2)) return false;
  return true;
}

void ObjectHeaderClass::Print(HANDLE hFile, FILE* out) {
  MyPrintFunc(out, L"GUID: ");
  KnownGuid.Print(hFile, out);
  MyPrintFunc(out, L"Date1: ");
  Date1.Print(out);
  MyPrintFunc(out, L"Date2: ");
  Date2.Print(out);
}

ObjectReferenceClass::ObjectReferenceClass()
{
}

ObjectReferenceClass::~ObjectReferenceClass()
{
}

ObjectReferenceClass* ObjectReferenceClass::Create(HANDLE hObjFile, std::vector<DWORD>& allocMap, LocationStruct &ls, bool bXP) {
  std::vector<ExtentClass> consumerRecordExtents;
  if (ls.IsValid()) {
    if (!GetRecordExtents(hObjFile, allocMap, ls, consumerRecordExtents))
      return 0;
    BYTE *recBuf = new BYTE[ls.Size];
    if (recBuf) {
      std::vector<ExtentClass>::iterator it = consumerRecordExtents.begin();
      DWORD currentIndex = 0;
      DWORD justread = 0;
      for (; it != consumerRecordExtents.end(); ++it) {
        LARGE_INTEGER offset;
        offset.QuadPart = it->GetStart();
        if (INVALID_SET_FILE_POINTER != SetFilePointer(hObjFile, offset.LowPart, &offset.HighPart, FILE_BEGIN)) {
          DWORD toRead = static_cast<DWORD>(it->GetCount() & ALL_BITS_32);
          if (::ReadFile(hObjFile, recBuf + currentIndex, toRead, &justread, NULL) && toRead == justread) {
            currentIndex += toRead;
          }
          else
            break;
        }
        else
          break;
      }
      if (currentIndex == ls.Size)
        return Create(recBuf, consumerRecordExtents, ls.Size, bXP);
    }
  }
  return 0;
}

ObjectReferenceClass* ObjectReferenceClass::Create(const void* recordBuf, std::vector<ExtentClass>& extents, uint32 size, bool bXP) {
  if (recordBuf && size) {
    ObjectReferenceClass *b = new ObjectReferenceClass;
    if (b) {
      uint64 currentoffset = 0;
      const BYTE * recordByteBuf = reinterpret_cast<const BYTE*>(recordBuf);
      DWORD currentsize = 0;
      if (currentoffset + sizeof(DWORD) < size) {
        currentsize = *reinterpret_cast<const DWORD*>(recordByteBuf + currentoffset);
        currentsize *= sizeof(wchar_t);
        currentoffset += sizeof(DWORD);
        if (currentoffset + currentsize < size) {
          std::vector<ExtentClass> recextents;
          CreateFieldExtents(currentoffset, currentsize, extents, recextents);
          b->Namespace.Set(recextents, TS_USTRING);
          currentoffset += currentsize;
        }
        else
          goto Exit;

        if (currentoffset + sizeof(DWORD) < size) {
          currentsize = *reinterpret_cast<const DWORD*>(recordByteBuf + currentoffset);
          currentsize *= sizeof(wchar_t);
          currentoffset += sizeof(DWORD);
          if (currentoffset + currentsize < size) {
            std::vector<ExtentClass> recextents;
            CreateFieldExtents(currentoffset, currentsize, extents, recextents);
            b->ClassName.Set(recextents, TS_USTRING);
            currentoffset += currentsize;
          }
          else
            goto Exit;
        }
        else
          goto Exit;

        if (currentoffset + sizeof(DWORD) < size) {
          currentsize = *reinterpret_cast<const DWORD*>(recordByteBuf + currentoffset);
          currentsize *= sizeof(wchar_t);
          currentoffset += sizeof(DWORD);
          if (currentoffset + currentsize < size) {
            std::vector<ExtentClass> recextents;
            CreateFieldExtents(currentoffset, currentsize, extents, recextents);
            b->PropertyName.Set(recextents, TS_USTRING);
            currentoffset += currentsize;
          }
          else
            goto Exit;
        }
        else
          goto Exit;

        if (currentoffset + sizeof(DWORD) < size) {
          currentsize = *reinterpret_cast<const DWORD*>(recordByteBuf + currentoffset);
          currentsize *= sizeof(wchar_t);
          currentoffset += sizeof(DWORD);
          if (currentoffset + currentsize <= size) {
            std::vector<ExtentClass> recextents;
            CreateFieldExtents(currentoffset, currentsize, extents, recextents);
            b->ObjectReferredPath.Set(recextents, TS_USTRING);
            currentoffset += currentsize;
          }
          else
            goto Exit;
        }
        else
          goto Exit;
        return b;
      }
    Exit:
      delete b;
    }
  }
  return 0;
}

bool ConstructInstanceRecord(std::string &strIn, InstanceStruct &fs) {
  bool ret = false;
  std::string str;
  if (char * strInstance = new char[strIn.length() + 1]) {
    if (!strcpy_s(strInstance, strIn.length() + 1, strIn.c_str())) {
      int index = 0;
      while (index < 3) {
        char *szDot = strrchr(strInstance, '.');
        if (!szDot)
          goto Exit;
        char *val = szDot + 1;
        *szDot = 0;
        if (!index)
          fs.Location.Size = atoll(val) & ALL_BITS_32;
        else if (1 == index)
          fs.Location.RecordID = atoll(val) & ALL_BITS_32;
        else {
          fs.Location.LogicalID = atoll(val) & ALL_BITS_32;
        }
        index++;
      }
      char *szUnderscore = strrchr(strInstance, '_');
      if (!szUnderscore)
        goto Exit;
      if (!SUCCEEDED(StringCbCopyA(fs.InstanceID, sizeof(fs.InstanceID), szUnderscore + 1)))
        goto Exit;
      ret = true;
    }
  Exit:
    delete[] strInstance;
  }
  return ret;
}