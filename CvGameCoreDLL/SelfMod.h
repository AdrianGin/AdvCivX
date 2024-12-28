// advc.092b: Let's put all self-modifying code in a single place
#pragma once
#ifndef SELF_MOD_H
#define SELF_MOD_H

// advc.002b:
typedef int FontResizeCallback(int iSize, int iSizeCategory, bool bBold, bool bItalic);

// Runtime modifications to the native code of Civ4BeyondSword.exe (v3.19)
class Civ4BeyondSwordPatches
{
public:
	void patchPlotIndicatorSize(); // (exposed to Python via CyGameCoreUtils) 
	bool isPlotIndicatorSizePatched() const { return m_bPlotIndicatorSizePatched; }
	// <advc.092c>
	void setHelpTextAreaSize(float fWidth); // (exposed to Python via CyGame)
	float getHelpTextAreaWidth() const { return m_fHelpTextAreaWidth; }
	bool isHelpTextAreaWidthPatched() const { return (getHelpTextAreaWidth() != 0); }
	// </advc.092c>
	// <advc.002b>
	void insertFontSizeHook(FontResizeCallback* pCallback);
	bool isFontSizeHookInserted() const { return (m_pCallback != NULL); }
	// </advc.002b>
	Civ4BeyondSwordPatches()
	:	m_bPlotIndicatorSizePatched(false),
		m_pCallback(NULL), m_pDSAddress(NULL), m_uiDSConstant(0),
		m_fHelpTextAreaWidth(0)
	{}

private:
	bool m_bPlotIndicatorSizePatched;
	// <advc.002b>
	FontResizeCallback* m_pCallback;
	uint* m_pDSAddress;
	uint m_uiDSConstant; // </advc.002b>
	float m_fHelpTextAreaWidth; // advc.092c
	void showErrorMsgToPlayer(CvWString szMsg);
	static int __cdecl fontSizeHook(); // advc.002b
	// advc.002b: Virtual only to prevent inlining
	virtual int resizeFontVirtual(int iNegativeSize) const;
};

namespace smc
{
	extern Civ4BeyondSwordPatches BtS_EXE;
}

#endif
