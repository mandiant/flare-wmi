#ifndef _DEFINED_EVENTCONSUMER_H
#define _DEFINED_EVENTCONSUMER_H

#include "Helper.h"
#include "ConsumerParser.h"

class EventConsumer : public ObjectHeaderClass {
public:
  EventConsumer() :
    ObjectHeaderClass(),
    CreatorSID(),
    MachineName(),
    MaximumQueueSize()
  {}

  EventConsumer(const EventConsumer &copyin) :
    ObjectHeaderClass(copyin),
    CreatorSID(copyin.CreatorSID),
    MachineName(copyin.MachineName),
    MaximumQueueSize(copyin.MaximumQueueSize)
  {}

  virtual void Print(HANDLE hFile, FILE *out);
  void SetMachineName(uint64 s, uint64 c, int type);
  void SetMachineName(std::vector<ExtentClass>& extents, int type);
  void SetCreatorSID(uint64 s, uint64 c);
  void SetCreatorSID(std::vector<ExtentClass>& extents);
  void SetMaximumQueueSize(uint32 val);
  EventConsumer& operator=(const EventConsumer &rhs);
  bool operator==(const EventConsumer &rhs) const;

  static EventConsumer* Create(HANDLE hObjFile, std::vector<DWORD>& allocMap, InstanceStruct &cs, const wchar_t* szType, bool bXP);
  static EventConsumer* Create(const void* recordBuf, std::vector<ExtentClass>& cRecordExtents, uint32 size, const wchar_t* szType, bool bXP);
  static EventConsumer* Create(const void* recordBuf, std::vector<ExtentClass>& cRecordExtents, uint32 size, bool bXP);

protected:
  ByteArrayValue  CreatorSID;
  StringValue     MachineName;
  Uint32Value     MaximumQueueSize;
};


#endif