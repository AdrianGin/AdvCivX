#pragma once

#ifndef COMBAT_ODDS_H
#define COMBAT_ODDS_H

// advc: Cut from CvGameCoreUtils.h

class CvUnit;

// advc: Renamed from "getCombatOdds"
int calculateCombatOdds(CvUnit const& kAttacker, CvUnit const& kDefender); // Exposed to Python

// <advc>
namespace combat_odds
{
class Combatant;
void initCombatants(CvUnit const& kAttacker, CvUnit const& kDefender,
		Combatant& att, Combatant& def, bool bHideFreeWins);
class Combatant // Replacing local iAttacker..., iDefender... variables
{
public:
	Combatant()
	:	m_iOdds(0), m_iHitsToWin(0), m_iCertainFS(0), m_iFSChances(0),
		m_iStrength(0), m_iDamagePerRound(0)
	{} // Will need both combatants for proper initilization (use initCombatants)
	void setOdds(int iOdds)
	{
		FAssert(iOdds >= 0);
		m_iOdds = iOdds;
	}
	void setHitsToWin(int iHitsToWin)
	{
		m_iHitsToWin = iHitsToWin;
	}
	// (advc: Moved this comment from BtS's getCombatOdds)
	// the integer math breaks down when #FS > 656 (with a die size of 1000)
	void setFirstStrikes(int iCertainFS, int iFSChances)
	{
		m_iCertainFS = iCertainFS;
		m_iFSChances = iFSChances;
	}
	void setStrength(int iStrength)
	{
		m_iStrength = iStrength;
	}
	void setDamagePerRound(int iDamagePerRound)
	{
		m_iDamagePerRound = iDamagePerRound;
	}
	// Per-round odds of landing a hit
	int odds() const { return m_iOdds; }
	// Hits that this combatant needs to land for victory
	int hitsToWin() const { return m_iHitsToWin; }
	// First-strike chances (not including guaranteed first strikes)
	int FSChances() const { return m_iFSChances; }
	// Guaranteed number of first strikes
	int lowFS() const { return m_iCertainFS; }
	// Maximally lucky number of first strikes
	int highFS() const { return m_iCertainFS + m_iFSChances; }
	// Current combat strength (not: firepower); needed by ACO.
	int strength() const { return m_iStrength; }
	// Damage that this combatant deals upon landing a hit
	int damagePerRound() const { return m_iDamagePerRound; }
private:
	int m_iOdds;
	int m_iHitsToWin;
	// Replacing m_iLowFS, m_iHighFS
	int m_iCertainFS;
	int m_iFSChances;
	int m_iStrength;
	int m_iDamagePerRound;
};
// From CvGameTextMgr.cpp (ACO helper function)
float getCombatOddsSpecific(CvUnit const& kAttacker, CvUnit const& kDefender,
		int iHitsByDef, int iHitsByAtt);

class CombatOutcome
{
public:
	CombatOutcome(int iHitsTakenAtt, int iHitsTakenDef, bool bWithdrawn)
	:	m_cHitsTakenAtt((char)iHitsTakenAtt), m_cHitsTakenDef((char)iHitsTakenDef),
		m_bWithdrawn(bWithdrawn) {}
	int getHitsTakenByAttacker() const { return m_cHitsTakenAtt; }
	int getHitsTakenByDefender() const { return m_cHitsTakenDef; }
	bool hasAttackerWithdrawn() const { return m_bWithdrawn; }
private:
	char m_cHitsTakenAtt;
	char m_cHitsTakenDef;
	bool m_bWithdrawn;
};

template<class Prob>
class OutcomeStats
{
public:
	OutcomeStats(bool bIgnoreFreeWins = false)
	:	m_bIgnoreFreeWins(bIgnoreFreeWins),
		m_iAttSurvival(0), m_iAttWithdrawal(0),
		m_iAttDecisiveVictory(0), m_iAttTacticalVictory(0)
	{}
	bool isIgnoreFreeWins() const { return m_bIgnoreFreeWins; }
	void add(CombatOutcome outcome, Prob pr)
	{
		m_distrib.push_back(std::make_pair(outcome, pr));
	}
	void calculateAttackerOdds(CvUnit const& kAttacker, CvUnit const& kDefender);
	void calculateAttackerOdds(Combatant const& kAtt, Combatant const& kDef);
	int getTraditionalCombatOdds() const { return m_iAttSurvival - m_iAttWithdrawal; }
private:
	std::vector<std::pair<CombatOutcome,Prob> > m_distrib;
	bool m_bIgnoreFreeWins;
	short m_iAttSurvival;
	short m_iAttWithdrawal;
	short m_iAttDecisiveVictory;
	short m_iAttTacticalVictory;
};
} // (end of combat_odds namespace)

typedef ScaledNum<64 * 1024, uint> ScaledOdds;
typedef combat_odds::OutcomeStats<float> FloatCombatOutcomes;
typedef combat_odds::OutcomeStats<ScaledOdds> ScaledCombatOutcomes;
void calculateCombatOutcomes(CvUnit const& kAttacker, CvUnit const& kDefender,
		FloatCombatOutcomes& kResult);
void calculateCombatOutcomes(CvUnit const& kAttacker, CvUnit const& kDefender,
		ScaledCombatOutcomes& kResult);
// </advc>

__int64 getBinomialCoefficient(int iN, int iK);

#endif
