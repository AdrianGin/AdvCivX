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
		Settings const& param) const {}

BestDefenderSelector::BestDefenderSelector(CvPlot const& kPlot)
:	DefenderSelector(kPlot) {}

BestDefenderSelector::~BestDefenderSelector() {}

// Cut from CvPlot::getBestDefender; functionally equivalent.
CvUnit* BestDefenderSelector::getDefender(Settings const& param) const
{
	// <advc> Ensure consistency of parameters
	FAssert(param.pAttUnit == NULL || param.pAttUnit->getOwner() == param.eAttOwner);
	// isEnemy implies isPotentialEnemy
	FAssert(!param.bTestAtWar || !param.bTestPotentialEnemy); // </advc>
	CvUnit* pBestDefender = NULL;
	int iBestUnitRank = -1;
	FOR_EACH_UNIT_VAR_IN(pLoopUnit, m_kPlot)
	{
		CvUnit& kUnit = *pLoopUnit;
		if (param.eDefOwner != NO_PLAYER &&
			kUnit.getOwner() != param.eDefOwner)
		{
			continue;
		}
		// advc: Was previously only checked with bTestCanMove - i.e. never.
		if (kUnit.isCargo())
			continue;
		// <advc> Moved the other conditions into CvUnit::canBeAttackedBy (new function)
		if (param.eAttOwner == NO_PLAYER ||
			kUnit.canBeAttackedBy(param.eAttOwner, param.pAttUnit,
			param.bTestAtWar, param.bTestPotentialEnemy,
			param.bTestVisible, // advc.028
			param.bTestCanAttack))
		{
			if (param.bTestAny)
				return &kUnit; // </advc>
			if (kUnit.isBetterDefenderThan(pBestDefender, param.pAttUnit,
				&iBestUnitRank, // UncutDragon
				param.bTestVisible)) // advc.061
			{
				pBestDefender = &kUnit;
			}
		}
	}
	// BETTER_BTS_AI_MOD: END
	return pBestDefender;
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

CvUnit* RandomizedSelector::getDefender(Settings const& param) const
{
	CvUnit* pRandDefender = NULL;
	std::vector<CvUnit*> defenders;
	getDefenders(defenders, param);
	if (defenders.empty())
	{	// If everyone is available, use the BtS algorithm.
		return BestDefenderSelector::getDefender(param);
	}
	int iBestUnitRank = -1;
	for (size_t i = 0; i < defenders.size(); i++)
	{
		if (defenders[i]->isBetterDefenderThan(pRandDefender, param.pAttUnit,
			&iBestUnitRank, param.bTestVisible))
		{
			pRandDefender = defenders[i];
		}
	}
	return pRandDefender;
}

void RandomizedSelector::getDefenders(std::vector<CvUnit*>& apDef,
	Settings const& param) const
{
	FAssert(apDef.empty());
	if (param.eAttOwner == NO_PLAYER)
	{	// Only valid in async code for plots that the active player can't attack
		return;
	}
	//PROFILE_FUNC(); // Ca. 1.5 permille of the running time
	validateCache(param.eAttOwner);
	for (int i = 0; i < m_cache.size() &&
		apDef.size() < (size_t)maxAvailableDefenders(); i++)
	{
		CvUnit* pUnit = ::getUnit(m_cache.at(i));
		if (pUnit == NULL)
		{	// But it could perhaps also be that the unit is currently dying; that would be OK.
			FAssertMsg(pUnit != NULL, "Cache out of date?");
			continue;
		}
		if (param.eDefOwner != NO_PLAYER && pUnit->getOwner() != param.eDefOwner)
			continue;
		if (pUnit->canBeAttackedBy(param.eAttOwner, param.pAttUnit,
			param.bTestAtWar, param.bTestPotentialEnemy,
			param.bTestVisible, // advc.028
			param.bTestCanAttack))
		{
			/*	Noncombatants are unavailable unless no proper defender is available:
				empty apDef means all are available. */
			if (canCombat(*pUnit, param))
				apDef.push_back(pUnit);
		}
	}
}

int RandomizedSelector::maxAvailableDefenders()
{
	// Tbd.: If the upper bound remains constant, move it to XML/ Globals.
	return 4; // GC.getMAX_AVAILABLE_DEFENDERS()
}

bool RandomizedSelector::canCombat(CvUnit const& kDefUnit, Settings const& param) const
{
	if (!kDefUnit.canFight())
		return false;
	if (!kDefUnit.isEnemy(TEAMID(param.eAttOwner)))
		return false;
	/*	Assume a land attacker unless a sea attacker is given. In particular,
		assume a land attacker when an air attacker is given. */
	bool bSeaAttacker = (param.pAttUnit != NULL &&
		param.pAttUnit->getDomainType() == DOMAIN_SEA);
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
	return kUnit.currHitPoints();
		// Bias for units with higher AI power value?
		//+ 2 * kUnit.getUnitInfo().getPower()
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
