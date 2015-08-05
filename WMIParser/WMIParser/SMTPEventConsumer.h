#include "Helper.h"
#include "EventConsumer.h"

class SMTPEventConsumerClass: public EventConsumer {
public:
  SMTPEventConsumerClass() :
    EventConsumer(),
    BccLine(),
    CcLine(),
    FromLine(),
    HeaderFields(),
    Message(),
    Name(),
    ReplyToLine(),
    SMTPServer(),
    Subject(),
    ToLine()
  {}

  SMTPEventConsumerClass(const SMTPEventConsumerClass &copyin) :
    EventConsumer(copyin),
    BccLine(copyin.BccLine),
    CcLine(copyin.CcLine),
    FromLine(copyin.FromLine),
    HeaderFields(copyin.HeaderFields),
    Message(copyin.Message),
    Name(copyin.Name),
    ReplyToLine(copyin.ReplyToLine),
    SMTPServer(copyin.SMTPServer),
    Subject(copyin.Subject),
    ToLine(copyin.ToLine)
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
  void SetSMTPServer(std::vector<ExtentClass>& extents, int type);
  void SetSubject(std::vector<ExtentClass>& extents, int type);
  void SetFromLine(std::vector<ExtentClass>& extents, int type);
  void SetMessage(std::vector<ExtentClass>& extents, int type);
  void SetToLine(std::vector<ExtentClass>& extents, int type);
  void SetCcLine(std::vector<ExtentClass>& extents, int type);
  void SetBccLine(std::vector<ExtentClass>& extents, int type);
  void SetReplyToLine(std::vector<ExtentClass>& extents, int type);
  void AddToHeaderFields(StringValue &str);

  static EventConsumer* Create(const void* recordBuf, std::vector<ExtentClass>& cRecordExtents, uint32 size, bool bXP);
  static bool IsConsumer(const void* recordBuf, uint32 size, bool bXP);

private:
  StringValue      BccLine;
  StringValue      CcLine;
  StringValue      FromLine;
  StringArrayValue HeaderFields;
  StringValue      Message;
  StringValue      Name;
  StringValue      ReplyToLine;
  StringValue      SMTPServer;
  StringValue      Subject;
  StringValue      ToLine;

  void SetName(uint64 s, uint64 c, int type);
  void SetSMTPServer(uint64 s, uint64 c, int type);
  void SetSubject(uint64 s, uint64 c, int type);
  void SetFromLine(uint64 s, uint64 c, int type);
  void SetMessage(uint64 s, uint64 c, int type);
  void SetToLine(uint64 s, uint64 c, int type);
  void SetCcLine(uint64 s, uint64 c, int type);
  void SetBccLine(uint64 s, uint64 c, int type);
  void SetReplyToLine(uint64 s, uint64 c, int type);
};