#include "Helper.h"
#include "EventConsumer.h"

class NTEventLogEventConsumerClass : public EventConsumer {
public:
  NTEventLogEventConsumerClass() :
    EventConsumer(),
    Category(),
    EventID(),
    EventType(1),                     //default is 1
    InsertionStringTemplates(),
    Name(),
    NameOfRawDataProperty(),
    NameoftheUserSIDProp(),
    NumberOfInsertionStrings(0),      //default is 0
    SourceName(),
    UNCServerName()
  {}

  NTEventLogEventConsumerClass(const NTEventLogEventConsumerClass &copyin) :
    EventConsumer(copyin),
    Category(copyin.Category),
    EventID(copyin.EventID),
    EventType(copyin.EventType),
    InsertionStringTemplates(copyin.InsertionStringTemplates),
    Name(copyin.Name),
    NameOfRawDataProperty(copyin.NameOfRawDataProperty),
    NameoftheUserSIDProp(copyin.NameoftheUserSIDProp),
    NumberOfInsertionStrings(copyin.NumberOfInsertionStrings),
    SourceName(copyin.SourceName),
    UNCServerName(copyin.UNCServerName)
  {
  }

  static const uint32 ConsumerDataTypesSize = 13;
  static const ConsumerDataType ConsumerDataTypes[ConsumerDataTypesSize];
  static const wchar_t CONSUMER_NAME[];
  //static const wchar_t GUID[];
  //static const wchar_t GUID_XP[];

  static const uint32 UNK_9_BYTES = 9;

  virtual void Print(HANDLE hFile, FILE *out);
  
  void SetName(std::vector<ExtentClass>& extents, int type);
  void SetUNCServerName(std::vector<ExtentClass>& extents, int type);
  void SetSourceName(std::vector<ExtentClass>& extents, int type);
  void SetNameOfRawDataProperty(std::vector<ExtentClass>& extents, int type);
  void SetNameoftheUserSIDProp(std::vector<ExtentClass>& extents, int type);
  
  void SetEventID(uint32 val);
  void SetEventType(uint32 val);
  void SetNumberOfInsertionStrings(uint32 val);
  void SetCategory(uint16 val);
  uint32 GetNumberOfInsertionStrings() { return NumberOfInsertionStrings.GetValue(); }
  void AddToInsertionStringTemplates(StringValue &str);
 
  static EventConsumer* Create(const void* recordBuf, std::vector<ExtentClass>& cRecordExtents, uint32 size, bool bXP);
  static bool IsConsumer(const void* recordBuf, uint32 size, bool bXP);

private:
  Uint16Value       Category;
  Uint32Value       EventID;
  Uint32Value       EventType;
  StringArrayValue  InsertionStringTemplates;
  StringValue       Name;
  StringValue       NameOfRawDataProperty;
  StringValue       NameoftheUserSIDProp;
  Uint32Value       NumberOfInsertionStrings;
  StringValue       SourceName;
  StringValue       UNCServerName;

  void SetName(uint64 s, uint64 c, int type);
  void SetUNCServerName(uint64 s, uint64 c, int type);
  void SetSourceName(uint64 s, uint64 c, int type);
  void SetNameOfRawDataProperty(uint64 s, uint64 c, int type);
  void SetNameoftheUserSIDProp(uint64 s, uint64 c, int type);
};