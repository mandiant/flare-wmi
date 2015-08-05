#ifndef _DEFINED_CLEC_H
#define _DEFINED_CLEC_H

#include "Helper.h"
#include "EventConsumer.h"

class CommandLineConsumerClass :public EventConsumer {
public:
  CommandLineConsumerClass() :
    EventConsumer(),
    CommandLineTemplate(),
    CreateNewConsole(0),                        //default is False
    CreateNewProcessGroup(ALL_BITS_16),         //default is True
    CreateSeparateWowVdm(0),                    //default is False
    CreateSharedWowVdm(0),                      //default is False
    DesktopName(),
    ExecutablePath(),
    FillAttributes(),
    ForceOffFeedback(0),                        //default is False
    ForceOnFeedback(0),                         //default is False
    KillTimeout(0),                             //default is 0x0
    Name(),
    Priority(0x20),                             //default is 0x20
    RunInteractively(0),                        //default is False
    ShowWindowCommand(),
    UseDefaultErrorMode(0),                     //default is False
    WindowTitle(),
    WorkingDirectory(),
    XCoordinate(),
    XNumCharacters(),
    XSize(),
    YCoordinate(),
    YNumCharacters(),
    YSize()
  {}

  CommandLineConsumerClass(const CommandLineConsumerClass &copyin) :
    EventConsumer(copyin),
    CommandLineTemplate(copyin.CommandLineTemplate),
    CreateNewConsole(copyin.CreateNewConsole),
    CreateNewProcessGroup(copyin.CreateNewProcessGroup),
    CreateSeparateWowVdm(copyin.CreateSeparateWowVdm),
    CreateSharedWowVdm(copyin.CreateSharedWowVdm),
    DesktopName(copyin.DesktopName),
    ExecutablePath(copyin.ExecutablePath),
    FillAttributes(copyin.FillAttributes),
    ForceOffFeedback(copyin.ForceOffFeedback),
    ForceOnFeedback(copyin.ForceOnFeedback),
    KillTimeout(copyin.KillTimeout),
    Name(copyin.Name),
    Priority(copyin.Priority),
    RunInteractively(copyin.RunInteractively),
    ShowWindowCommand(copyin.ShowWindowCommand),
    UseDefaultErrorMode(copyin.UseDefaultErrorMode),
    WindowTitle(copyin.WindowTitle),
    WorkingDirectory(copyin.WorkingDirectory),
    XCoordinate(copyin.XCoordinate),
    XNumCharacters(copyin.XNumCharacters),
    XSize(copyin.XSize),
    YCoordinate(copyin.YCoordinate),
    YNumCharacters(copyin.YNumCharacters),
    YSize(copyin.YSize)
  {}

  static const uint32 ConsumerDataTypesSize = 27;
  static const ConsumerDataType ConsumerDataTypes[ConsumerDataTypesSize];
  static const wchar_t CONSUMER_NAME[];
  //static const wchar_t GUID[];
  //static const wchar_t GUID_XP[];

  static const uint32 UNK_C_BYTES = 0xC;

  virtual  void Print(HANDLE hFile, FILE *out);
  void SetName(std::vector<ExtentClass>& extents, int type);
  void SetExecutablePath(std::vector<ExtentClass>& extents, int type);
  void SetCommandLineTemplate(std::vector<ExtentClass>& extents, int type);
  void SetWorkingDirectory(std::vector<ExtentClass>& extents, int type);
  void SetDesktopName(std::vector<ExtentClass>& extents, int type);
  void SetWindowTitle(std::vector<ExtentClass>& extents, int type);
  void SetKillTimeout(uint32 val);
  void SetXCoordinate(uint32 val);
  void SetYCoordinate(uint32 val);
  void SetXSize(uint32 val);
  void SetYSize(uint32 val);
  void SetXNumCharacters(uint32 val);
  void SetYNumCharacters(uint32 val);
  void SetFillAttributes(uint32 val);
  void SetShowWindowCommand(uint32 val);
  void SetPriority(sint32 dataVal);
  void SetUseDefaultErrorMode(uint16 value);
  void SetCreateNewConsole(uint16 value);
  void SetCreateNewProcessGroup(uint16 value);
  void SetCreateSeparateWowVdm(uint16 value);
  void SetCreateSharedWowVdm(uint16 value);
  void SetForceOnFeedback(uint16 value);
  void SetForceOffFeedback(uint16 value);
  void SetRunInteractively(uint16 value);

  static EventConsumer* Create(const void* recordBuf, std::vector<ExtentClass>& cRecordExtents, uint32 size, bool bXP);
  static bool IsConsumer(const void* recordBuf, uint32 size, bool bXP);

private:
  StringValue   CommandLineTemplate;
  BoolValue     CreateNewConsole;
  BoolValue     CreateNewProcessGroup;
  BoolValue     CreateSeparateWowVdm;
  BoolValue     CreateSharedWowVdm;
  StringValue   DesktopName;
  StringValue   ExecutablePath;
  Uint32Value   FillAttributes;
  BoolValue     ForceOffFeedback;
  BoolValue     ForceOnFeedback;
  Uint32Value   KillTimeout;
  StringValue   Name;
  Sint32Value   Priority;
  BoolValue     RunInteractively;
  Uint32Value   ShowWindowCommand;
  BoolValue     UseDefaultErrorMode;
  StringValue   WindowTitle;
  StringValue   WorkingDirectory;
  Uint32Value   XCoordinate;
  Uint32Value   XNumCharacters;
  Uint32Value   XSize;
  Uint32Value   YCoordinate;
  Uint32Value   YNumCharacters;
  Uint32Value   YSize;

  void SetName(uint64 s, uint64 c, int type);
  void SetExecutablePath(uint64 s, uint64 c, int type);
  void SetCommandLineTemplate(uint64 s, uint64 c, int type);
  void SetWorkingDirectory(uint64 s, uint64 c, int type);
  void SetDesktopName(uint64 s, uint64 c, int type);
  void SetWindowTitle(uint64 s, uint64 c, int type);
};
#endif