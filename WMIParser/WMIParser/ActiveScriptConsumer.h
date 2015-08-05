#ifndef _DEFINED_ASEC_H
#define _DEFINED_ASEC_H
#include "Helper.h"

class ActiveScriptConsumerClass : public EventConsumer{
public:
  ActiveScriptConsumerClass() :
    EventConsumer(),
    Name(),
    ScriptingEngine(),
    ScriptText(),
    ScriptFilename(),
    KillTimeout(0)        //default is 0
    
  {}

  ActiveScriptConsumerClass(const ActiveScriptConsumerClass &copyin) :
    EventConsumer(copyin),
    Name(copyin.Name),
    ScriptingEngine(copyin.ScriptingEngine),
    ScriptText(copyin.ScriptText),
    ScriptFilename(copyin.ScriptFilename),
    KillTimeout(copyin.KillTimeout)
  {
  }

  static const uint32 ConsumerDataTypesSize = 8;
  static const ConsumerDataType ConsumerDataTypes[ConsumerDataTypesSize];
  static const wchar_t CONSUMER_NAME[];
  static const uint32 UNK_7_BYTES = 7;

  virtual void Print(HANDLE hFile, FILE *out);

  void SetName(std::vector<ExtentClass>& extents, int type);
  void SetScriptingEngine(std::vector<ExtentClass>& extents, int type);
  void SetScriptText(std::vector<ExtentClass>& extents, int type);
  void SetScriptFilename(std::vector<ExtentClass>& extents, int type);
  void SetKillTimeout(uint32 val);

  static EventConsumer* Create(const void* recordBuf, std::vector<ExtentClass>& cRecordExtents, uint32 size, bool bXP);
  static bool IsConsumer(const void* recordBuf, uint32 size, bool bXP);

private:
  Uint32Value  KillTimeout;
  StringValue  Name;
  StringValue  ScriptingEngine;
  StringValue  ScriptFilename;
  StringValue  ScriptText;

  void SetName(uint64 s, uint64 c, int type);
  void SetScriptingEngine(uint64 s, uint64 c, int type);
  void SetScriptText(uint64 s, uint64 c, int type);
  void SetScriptFilename(uint64 s, uint64 c, int type);
};
#endif