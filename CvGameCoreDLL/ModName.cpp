#include "CvGameCoreDLL.h"
#include "ModName.h"

// advc.106i: New implementation file; see comment in header.

void ModName::update(char const* szFullPath, char const* szPathInRoot)
{
	m_sFullPath = szFullPath;
	m_sPathInRoot = szPathInRoot;
	m_sName = m_sPathInRoot;
	size_t posMods = m_sName.find("Mods");
	if (posMods != CvString::npos)
	{
		/*	Skip over "Mods" plus the path separator.
			And chop off the separator at the end. */
		m_sName = m_sName.substr(posMods + 5, m_sName.length() - posMods - 6);
	}
	updateUserPath(); // advc.009
}

// advc.009:
void ModName::updateUserPath()
{
	if (!m_sUserPath.empty())
		return;
	uint const pDSAddress = 0x00C87160;
	uint const pDSAddressSteam = 0x00C2A158;
	/*	Some safety measures. First, check that the data segment address
		where I've seen the My Games path appears in the binary in the place
		I expect it to appear. */
	uint* const pDSAddrLoc = reinterpret_cast<uint*>(0x00411D67);
	uint* const pDSAddrLocSteam = reinterpret_cast<uint*>(0x004123C7);
	uint* pInitData = NULL;
	if (*pDSAddrLoc == pDSAddress)
		pInitData = *reinterpret_cast<uint**>(pDSAddress);
	else if (*pDSAddrLocSteam == pDSAddressSteam)
		pInitData = *reinterpret_cast<uint**>(pDSAddressSteam);
	if (pInitData == NULL)
		return;
	int const iDwordOffset = 14;
	// Sanity check for safe dereferencing of suspected C string
	if (pInitData[iDwordOffset] < 0x00010000 || pInitData[iDwordOffset] > 0x01000000)
		return;
	char const* szConfigPath = reinterpret_cast<char const*>(pInitData[14]);
	// Look for a terminating char within a reasonable length of bytes
	bool bString = false;
	for (int i = 0; i < 1024; i++)
	{
		if (szConfigPath[i] == '\0')
		{
			bString = true;
			break;
		}
	}
	if (!bString)
		return;
	CvString sUserPath(reinterpret_cast<char const*>(pInitData[14]));
	// "B/beyond the S/sword" should be somewhere in this path
	if (sUserPath.find("eyond") == CvString::npos)
		sUserPath.clear();
	else sUserPath.append(getName());
	if (!sUserPath.empty())
		m_sUserPath = sUserPath;
}