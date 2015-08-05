// stdafx.h : include file for standard system include files,
// or project specific include files that are used frequently, but
// are changed infrequently
//

#pragma once

#include "targetver.h"

#include <stdio.h>
#include <tchar.h>
#include <windows.h>
#include <strsafe.h>
#include <stdlib.h>
#include <stdarg.h>
#include <WTypes.h>
#include "includevld.h"

//#ifdef _WIN64
//typedef unsigned long uint64;
//typedef long          int64;
//#else
typedef unsigned long long uint64;
typedef long long          int64;
//#endif


typedef unsigned char  byte;
typedef unsigned short uint16;
typedef short          sint16;
typedef unsigned int   uint32;
typedef int            sint32;

const uint32 PAGE_SIZE = 8192;

#define ALL_BITS_16 0xFFFF
#define ALL_BITS_32 0xFFFFFFFF

#define FILTERTOCONSUMER_BASE_CLASS L"__FilterToConsumerBinding"
#define FILTER_BASE_CLASS      L"__EventFilter"
#define CONSUMER_BASE_CLASS    L"__EventConsumer"
#define NAMESPACE_BASE_CLASS   L"__namespace"
#define NAMESPACE_ROOT         L"ROOT"
#define NAMESPACE_PREFIX       "NS_"
#define CLASS_PREFIX           "CR_"
#define INSTANCE_PREFIX        "CI_"
#define INSTANCE2_PREFIX       "KI_"
#define INSTANCE_NAME_PREFIX   "IL_"
#define REFERENCE_PREFIX       "IR_"
#define REFERENCE_NAME_PREFIX  "R_"
#define CLASS_SUB_PREFIX       "C_"
#define CLASS_DEF_PREFIX       "CD_"

// TODO: reference additional headers your program requires here
