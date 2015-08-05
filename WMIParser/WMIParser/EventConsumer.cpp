#include "stdafx.h"
#include "EventConsumer.h"
#include "ActiveScriptConsumer.h"
#include "CommandLineConsumer.h"
#include "NTEventLogEventConsumer.h"
#include "LogFileEventConsumer.h"
#include "SMTPEventConsumer.h"

void EventConsumer::SetMachineName(uint64 s, uint64 c, int type) {
  MachineName.Set(s, c, type);
}

void EventConsumer::SetMachineName(std::vector<ExtentClass>& extents, int type) {
  if (extents.size() == 1)
    MachineName.Set(extents.at(0).GetStart(), extents.at(0).GetCount(), type);
  else
    MachineName.Set(extents, type);
}

void EventConsumer::SetCreatorSID(uint64 s, uint64 c) {
  CreatorSID.Set(s, c);
}

void EventConsumer::SetCreatorSID(std::vector<ExtentClass>& extents) {
  if (extents.size() == 1)
    CreatorSID.Set(extents.at(0).GetStart(), extents.at(0).GetCount());
  else
    CreatorSID.Set(extents);
}


void EventConsumer::SetMaximumQueueSize(uint32 val) {
  MaximumQueueSize = val;
}

EventConsumer& EventConsumer::operator=(const EventConsumer &rhs)
{
  __super::operator=(rhs);
  this->CreatorSID = rhs.CreatorSID;
  this->MachineName = rhs.MachineName;
  this->MaximumQueueSize = rhs.MaximumQueueSize;

  return *this;
}

bool EventConsumer::operator==(const EventConsumer &rhs) const
{
  if (!__super::operator==(rhs)) return false;
  if (!(this->CreatorSID == rhs.CreatorSID)) return false;
  if (!(this->MachineName == rhs.MachineName)) return false;
  if (!(this->MaximumQueueSize == rhs.MaximumQueueSize)) return false;
  return true;
}

void EventConsumer::Print(HANDLE hFile, FILE *out) {
  __super::Print(hFile, out);
  MyPrintFunc(out, L"CreatorSID: ");
  CreatorSID.Print(hFile, out);
  MyPrintFunc(out, L"MachineName: ");
  MachineName.Print(hFile, out);
  MyPrintFunc(out, L"MaximumQueueSize: ");
  MaximumQueueSize.Print(out);
}

EventConsumer* EventConsumer::Create(HANDLE hObjFile, std::vector<DWORD>& allocMap, InstanceStruct &cs, const wchar_t* szType, bool bXP) {
  std::vector<ExtentClass> consumerRecordExtents;
  EventConsumer* p = 0;
  if (cs.IsValid())
    if (!GetRecordExtents(hObjFile, allocMap, cs.Location, consumerRecordExtents))
      return 0;
  BYTE *recBuf = new BYTE[cs.Location.Size];
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
    if (currentIndex == cs.Location.Size)
      p = szType ? Create(recBuf, consumerRecordExtents, cs.Location.Size, szType, bXP) : Create(recBuf, consumerRecordExtents, cs.Location.Size, bXP);
    delete[] recBuf;
  }
  return p;
}

EventConsumer* EventConsumer::Create(const void* recordBuf, std::vector<ExtentClass>& cRecordExtents, uint32 size, const wchar_t* szType, bool bXP) {
  EventConsumer* p = 0;
  if (cRecordExtents.size()) {
    uint64 offset = cRecordExtents.at(0).GetStart();
    if (!_wcsicmp(szType, L"CommandLineEventConsumer")) {
      wprintf(L"CommandLineEventConsumer : Found the record at offset (%I64d)\r\n", offset);
      p = CommandLineConsumerClass::Create(recordBuf, cRecordExtents, size, bXP);
    }
    else if (!_wcsicmp(szType, L"ActiveScriptEventConsumer")) {
      wprintf(L"ActiveScriptEventConsumer : Found the record at offset (%I64d)\r\n", offset);
      p = ActiveScriptConsumerClass::Create(recordBuf, cRecordExtents, size, bXP);
    }
    else if (!_wcsicmp(szType, L"NTEventLogEventConsumer")) {
      wprintf(L"NTEventLogEventConsumer : Found the record at offset (%I64d)\r\n", offset);
      p = NTEventLogEventConsumerClass::Create(recordBuf, cRecordExtents, size, bXP);
    }
    else if (!_wcsicmp(szType, L"LogFileEventConsumer")) {
      wprintf(L"LogFileEventConsumer : Found the record at offset (%I64d)\r\n", offset);
      p = LogFileEventConsumerClass::Create(recordBuf, cRecordExtents, size, bXP);
    }
    else if (!_wcsicmp(szType, L"SMTPEventConsumer")) {
      wprintf(L"SMTPEventConsumer : Found the record at offset (%I64d)\r\n", offset);
      p = SMTPEventConsumerClass::Create(recordBuf, cRecordExtents, size, bXP);
    }
  }
  return p;
}

EventConsumer* EventConsumer::Create(const void* recordBuf, std::vector<ExtentClass>& cRecordExtents, uint32 size, bool bXP) {
  EventConsumer* p = 0;
  if (cRecordExtents.size()) {
    uint64 offset = cRecordExtents.at(0).GetStart();
    if (CommandLineConsumerClass::IsConsumer(recordBuf, size, bXP)) {
      wprintf(L"CommandLineEventConsumer : Found the record at offset (%I64d)\r\n", offset);
      p = CommandLineConsumerClass::Create(recordBuf, cRecordExtents, size, bXP);
    }
    else if (ActiveScriptConsumerClass::IsConsumer(recordBuf, size, bXP)) {
      wprintf(L"ActiveScriptEventConsumer : Found the record at offset (%I64d)\r\n", offset);
      p = ActiveScriptConsumerClass::Create(recordBuf, cRecordExtents, size, bXP);
    }
    else if (NTEventLogEventConsumerClass::IsConsumer(recordBuf, size, bXP)) {
      wprintf(L"NTEventLogEventConsumer : Found the record at offset (%I64d)\r\n", offset);
      p = NTEventLogEventConsumerClass::Create(recordBuf, cRecordExtents, size, bXP);
    }
    else if (LogFileEventConsumerClass::IsConsumer(recordBuf, size, bXP)) {
      wprintf(L"LogFileEventConsumer : Found the record at offset (%I64d)\r\n", offset);
      p = LogFileEventConsumerClass::Create(recordBuf, cRecordExtents, size, bXP);
    }
    else if (SMTPEventConsumerClass::IsConsumer(recordBuf, size, bXP)) {
      wprintf(L"SMTPEventConsumer : Found the record at offset (%I64d)\r\n", offset);
      p = SMTPEventConsumerClass::Create(recordBuf, cRecordExtents, size, bXP);
    }
  }
  return p;
}