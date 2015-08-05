#include "Helper.h"
#include "EventConsumer.h"

class LogFileEventConsumerClass : public EventConsumer {
public:
  LogFileEventConsumerClass() :
    EventConsumer(),
    FileName(),
    Name(),
    Text(),
    MaximumFileSize(ALL_BITS_16), // default is 65535
    IsUnicode(0)
  {}

  LogFileEventConsumerClass(const LogFileEventConsumerClass &copyin) : 
    EventConsumer(copyin),
    FileName(copyin.FileName),
    Name(copyin.Name),
    Text(copyin.Text),
    MaximumFileSize(copyin.MaximumFileSize),
    IsUnicode(copyin.IsUnicode)
  {
  }

  static const uint32 ConsumerDataTypesSize = 8;
  static const ConsumerDataType ConsumerDataTypes[ConsumerDataTypesSize];
  static const wchar_t CONSUMER_NAME[];
  static const uint32 UNK_7_BYTES = 7;

  
  void SetName(std::vector<ExtentClass>& extents, int type);
  void SetFilename(std::vector<ExtentClass>& extents, int type);
  void SetText(std::vector<ExtentClass>& extents, int type);
  void SetIsUnicode(uint16 value);
  void SetMaximumFileSize(uint64 dataVal);
  virtual void Print(HANDLE hFile, FILE *out);

  static EventConsumer* Create(const void* recordBuf, std::vector<ExtentClass>& cRecordExtents, uint32 size, bool bXP);
  static bool IsConsumer(const void* recordBuf, uint32 size, bool bXP);

private:
  StringValue   FileName;
  BoolValue        IsUnicode;
  Uint64Value      MaximumFileSize;
  StringValue   Name;
  StringValue   Text;

  void SetName(uint64 s, uint64 c, int type);
  void SetFilename(uint64 s, uint64 c, int type);
  void SetText(uint64 s, uint64 c, int type);
};