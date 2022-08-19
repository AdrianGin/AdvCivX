#include "CvGameCoreDLL.h"
#include "DefenderSelector.h"
#include "CvUnit.h"
#include "CvPlot.h"
#include "CvGamePlay.h"
#include "CvGlobals.h"

DefenderSelector::DefenderSelector(CvPlot const& kPlot) : m_kPlot(kPlot) {}

DefenderSelector::~DefenderSelector() {}

void DefenderSelector::uninit() {}

void DefenderSelector::update() {}

void DefenderSelector::getDefenders(std::vector<CvUnit*>& apDef,
		PlayerTypes eOwner, DefenderFilters& kFilters) const {}

BestDefenderSelector::BestDefenderSelector(CvPlot const& kPlot)
:	DefenderSelector(kPlot) {}

BestDefenderSelector::~BestDefenderSelector() {}

/*	Cut from CvPlot::getBestDefender; functionally equivalent unless
	a comment says otherwise. */
CvUnit* BestDefenderSelector::getDefender(PlayerTypes eOwner, 
	DefenderFilters& kFilters) const
{
	// Ensure consistency of parameters
	if (kFilters.m_pAttacker != NULL)
	{
		FAssert(kFilters.m_pAttacker->getOwner() == kFilters.m_eAttackingPlayer);
		kFilters.m_eAttackingPlayer = kFilters.m_pAttacker->getOwner();
	}
	// isEnemy implies isPotentialEnemy
	FAssert(!kFilters.m_bTestEnemy || !kFilters.m_bTestPotentialEnemy); // </advc>
	// BETTER_BTS_AI_MOD, Lead From Behind (UncutDragon), 02/21/10, jdog5000
	int iBestUnitRank = -1;
	CvUnit* pBestUnit = NULL;
	FOR_EACH_UNIT_VAR_IN(pLoopUnit, m_kPlot)
	{
		CvUnit& kUnit = *pLoopUnit;
		if (eOwner != NO_PLAYER && kUnit.getOwner() != eOwner)
			continue;
		if (kUnit.isCargo()) // advc: Was previously only checked with TestCanMove
			continue;
		if (kFilters.m_bTestCanMove && !kUnit.canMove())
			continue;
		// <advc> Moved the other conditions into CvUnit::canBeAttackedBy (new function)
		if (kFilters.m_eAttackingPlayer == NO_PLAYER ||
			kUnit.canBeAttackedBy(kFilters.m_eAttackingPlayer,
			kFilters.m_pAttacker, kFilters.m_bTestEnemy, kFilters.m_bTestPotentialEnemy,
			kFilters.m_bTestVisible, // advc.028
			kFilters.m_bTestCanAttack))
		{
			if (kFilters.m_bTestAny)
				return &kUnit; // </advc>
			if (kUnit.isBetterDefenderThan(pBestUnit, kFilters.m_pAttacker,
				&iBestUnitRank, // UncutDragon
				kFilters.m_bTestVisible)) // advc.061
			{
				pBestUnit = &kUnit;
			}
		}
	}
	// BETTER_BTS_AI_MOD: END
	return pBestUnit;
}

RandomizedSelector::RandomizedSelector(CvPlot const& kPlot) : BestDefenderSelector(kPlot) {}

RandomizedSelector::~RandomizedSelector() {}

void RandomizedSelector::uninit()
{
	m_cache.clear();
}

void RandomizedSelector::update()
{
	m_cache.setValid(false); // Recompute only on demand
}

CvUnit* RandomizedSelector::getDefender(PlayerTypes eOwner, 
	DefenderFilters& kFilters) const
{
	CvUnit* pRandDefender = NULL;
	std::vector<CvUnit*> defenders;
	getDefenders(defenders, eOwner, kFilters);
	if (defenders.empty())
	{	// If everyone is available, use the BtS algorithm.
		return BestDefenderSelector::getDefender(eOwner, kFilters);
	}
	int iBestUnitRank = -1;
	for (size_t i = 0; i < defenders.size(); i++)
	{
		if (defenders[i]->isBetterDefenderThan(pRandDefender, kFilters.m_pAttacker,
			&iBestUnitRank, kFilters.m_bTestVisible))
		{
			pRandDefender = defenders[i];
		}
	}
	return pRandDefender;
}

void RandomizedSelector::getDefenders(std::vector<CvUnit*>& apDef,
	PlayerTypes eOwner, DefenderFilters& kFilters) const
{
	FAssert(apDef.empty());
	if (kFilters.m_eAttackingPlayer == NO_PLAYER)
	{	// Only valid in async code for plots that the active player can't attack
		return;
	}
	//PROFILE_FUNC(); // Ca. 1.5 permille of the running time
	validateCache(kFilters.m_eAttackingPlayer);
	for (int i = 0; i < m_cache.size() &&
		apDef.size() < (size_t)maxAvailableDefenders(); i++)
	{
		CvUnit* pUnit = ::getUnit(m_cache.at(i));
		if (pUnit == NULL)
		{	// But it could perhaps also be that the unit is currently dying; that would be OK.
			FAssertMsg(pUnit != NULL, "Cache out of date?");
			continue;
		}
		if (eOwner != NO_PLAYER && pUnit->getOwner() != eOwner)
			continue;
		if (pUnit->canBeAttackedBy(kFilters.m_eAttackingPlayer,
			kFilters.m_pAttacker,
			kFilters.m_bTestEnemy, kFilters.m_bTestPotentialEnemy,
			kFilters.m_bTestVisible, // advc.028
			kFilters.m_bTestCanAttack))
		{
			/*	Noncombatants are unavailable unless no proper defender is available:
				empty apDef means all are available. */
			if (canCombat(*pUnit, kFilters))
				apDef.push_back(pUnit);
		}
	}
}

int RandomizedSelector::maxAvailableDefenders()
{
	// Tbd.: If the upper bound remains constant, move it to XML/ Globals.
	return 4; // GC.getMAX_AVAILABLE_DEFENDERS()
}

bool RandomizedSelector::canCombat(CvUnit const& kDefUnit,
	DefenderFilters const& kFilters) const
{
	if (!kDefUnit.canFight())
		return false;
	if (!kDefUnit.isEnemy(TEAMID(kFilters.m_eAttackingPlayer)))
		return false;
	/*	Assume a land attacker unless a sea attacker is given. In particular,
		assume a land attacker when an air attacker is given. */
	bool bSeaAttacker = (kFilters.m_pAttacker != NULL &&
		kFilters.m_pAttacker->getDomainType() == DOMAIN_SEA);
	if (!bSeaAttacker && !m_kPlot.isWater() &&
		(kDefUnit.getDomainType() != DOMAIN_LAND || kDefUnit.isCargo()))
	{
		return false;
	}
	return true;
}

void RandomizedSelector::validateCache(PlayerTypes eAttackerOwner) const
{
	if (!m_cache.isValid())
		cacheDefenders(eAttackerOwner);
	/*	Tbd. Call DefenderSelector::update as described below.
		However, the time saved is going to be negligible, so this may not be
		worth polluting the code base, and isn't a priority in any case.
		- from CvUnit::kill (update the plot where the unit was killed) and
		  on non-lethal damage (but not while combat is still being resolved)
		- from CvUnit::setXY (on the source and destination plot)
		- at the start of each CvPlayer's turn (all plots)
		- from CvTeam::declareWar and makePeace (only plots with military units
		  owned by the war target)
		 Updates after combat should also write a message to the combat log.
		 And when the active player destroys a defender in combat, the on-screen
		 message should say which unit has become available. */
	// For now, keep the cache permanently invalid.
	//m_cache.setValid(true);
}

void RandomizedSelector::cacheDefenders(PlayerTypes eAttackerOwner) const
{
	PROFILE_FUNC(); // Less than 1 permille of the running time
	m_cache.clear(m_kPlot.getNumUnits());
	FOR_EACH_UNIT_IN(pUnit, m_kPlot)
	{
		if (pUnit == NULL)
		{
			// Might be OK; if defenders get cached while units are dying ...
			FAssert(pUnit != NULL);
			continue;
		}
		int iAvailability = biasValue(*pUnit) *
				(50 + randomValue(*pUnit, eAttackerOwner));
		m_cache.add(pUnit->getIDInfo(), iAvailability);
	}
	m_cache.sort();
}

int RandomizedSelector::biasValue(CvUnit const& kUnit) const
{
	// Prefer high defensive modifier (but exclude generic extra combat modifier)
	CombatDetails cd;
	kUnit.maxCombatStr(kUnit.plot(), NULL, &cd);
	return kUnit.currHitPoints() * (100 + cd.iModifierTotal - cd.iExtraCombatPercent);
		// Minor bias for strong units?
		//+ cd.iBaseCombatStr
}

int RandomizedSelector::randomValue(CvUnit const& kUnit, PlayerTypes eAttackerOwner) const
{
	std::vector<int> hashInputs;
	hashInputs.push_back(GC.getGame().getGameTurn());
	hashInputs.push_back(eAttackerOwner);
	hashInputs.push_back(kUnit.getOwner());
	hashInputs.push_back(kUnit.getID());
	hashInputs.push_back(m_kPlot.getX());
	hashInputs.push_back(m_kPlot.getY());
	/*	Let the hash function use eAttackerOwner's starting coordinates
		as a sort of game id */
	return scaled::hash(hashInputs, eAttackerOwner).getPercent();
}

RandomizedSelector::Cache::Cache() : m_bValid(false) {}

void RandomizedSelector::Cache::setValid(bool b)
{
	m_bValid = b;
}

void RandomizedSelector::Cache::clear(int iReserve)
{
	m_entries.clear();
	setValid(false);
	if (iReserve > 0) // Just for performance
		m_entries.reserve(iReserve);
}

bool RandomizedSelector::Cache::isValid() const
{
	return m_bValid;
}

IDInfo RandomizedSelector::Cache::at(int iPosition) const
{
	return m_entries.at(iPosition).second;
}

int RandomizedSelector::Cache::size() const
{
	return (int)m_entries.size();
}

void RandomizedSelector::Cache::add(IDInfo id, int iValue)
{
	m_entries.push_back(CacheEntry(iValue, id));
}

void RandomizedSelector::Cache::sort()
{
	// No point in stable_sort as the cache is fully recomputed before sorting
	std::sort(m_entries.rbegin(), m_entries.rend());
}
