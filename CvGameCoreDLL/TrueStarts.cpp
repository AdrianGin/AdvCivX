// advc.tsl: New file; see comments in header.

#include "CvGameCoreDLL.h"
#include "TrueStarts.h"
#include "CvInfo_TrueStarts.h"
#include "CvInfo_Terrain.h"
#include "CvMap.h"
#include "CvArea.h"
#include "CvGamePlay.h"
#include "PlotRange.h"
#include "BBAILog.h"

using std::auto_ptr;

// To enable, toggle 'false' to 'true' and also enable BBAI map logging.
#define IFLOG if (gMapLogLevel > 0 && bLog && false)


namespace
{
	/*	Treating peaks as continental boundaries is useful for game balance,
		but, here, we should care more about the intuitive impression that
		players have of the terrain surrounding the starting plot of a civ.
		Also makes life easier when counting peaks for relief-based preferences. */
	bool sameArea(CvPlot const& kFirst, CvPlot const& kSecond)
	{
		if (GC.getDefineBOOL(CvGlobals::PASSABLE_AREAS))
		{
			return (kFirst.getArea().getRepresentativeArea() ==
					kSecond.getArea().getRepresentativeArea());
		}
		return kFirst.sameArea(kSecond);
	}
}


TrueStarts::TrueStarts()
{
	// The official non-Earth scenarios set all latitude values to 0
	m_bMapHasLatitudes = (GC.getMap().getTopLatitude() >
			GC.getMap().getBottomLatitude());
	FOR_EACH_ENUM(TruCiv)
	{
		m_truCivs.set(GC.getInfo(eLoopTruCiv).getCiv(),
				&GC.getInfo(eLoopTruCiv));
	}
	// Ignore the truLeader info when leaders are unrestricted
	if (!GC.getGame().isOption(GAMEOPTION_LEAD_ANY_CIV))
	{
		FOR_EACH_ENUM(TruLeader)
		{
			m_truLeaders.set(GC.getInfo(eLoopTruLeader).getLeader(),
					&GC.getInfo(eLoopTruLeader));
		}
	}
	FOR_EACH_ENUM(TruBonus)
	{
		m_truBonuses.set(GC.getInfo(eLoopTruBonus).getBonus(),
				&GC.getInfo(eLoopTruBonus));
	}
	FOR_EACH_ENUM(Civilization)
	{
		FOR_EACH_ENUM(Bonus)
		{
			if (isTruBonusDiscouraged(m_truBonuses.get(eLoopBonus), eLoopCivilization))
				m_discouragedBonusesTotal.add(eLoopCivilization, 1);
			if (isTruBonusEncouraged(m_truBonuses.get(eLoopBonus), eLoopCivilization))
				m_encouragedBonusesTotal.add(eLoopCivilization, 1);
		}
	}
	m_radii.reset();
	for (PlayerIter<CIV_ALIVE> itPlayer; itPlayer.hasNext(); ++itPlayer)
		calculateRadius(*itPlayer);
	m_plotWeights.reset();
	for (PlayerIter<CIV_ALIVE> itPlayer; itPlayer.hasNext(); ++itPlayer)
		calculatePlotWeights(*itPlayer);
	/*	Would be nicer to cache these at CvGlobals (as the Global Warming code
		uses them too), but that's a bit annoying to implement. Also, this way,
		I can use the names most appropriate for the True Starts option. */
	m_eWarmForest = (FeatureTypes)GC.getDefineINT("WARM_FEATURE");
	m_eCoolForest = (FeatureTypes)GC.getDefineINT("TEMPERATE_FEATURE");
	/*	(Woods should be the natural vegetation of the biome represented by
		this terrain type) */
	m_eWoodland = (TerrainTypes)GC.getDefineINT("TEMPERATE_TERRAIN");
	m_eSteppe = (TerrainTypes)GC.getDefineINT("DRY_TERRAIN");
	m_eTundra = (TerrainTypes)GC.getDefineINT("COLD_TERRAIN");
	m_eDesert = (TerrainTypes)GC.getDefineINT("BARREN_TERRAIN");
	m_ePolarDesert = (TerrainTypes)GC.getDefineINT("FROZEN_TERRAIN");
}

namespace
{
	// Wrapper for convenience
	bool canHaveBonus(CvPlot const& kPlot, BonusTypes eBonus,
		bool bIgnoreFeature = false)
	{
		return kPlot.canHaveBonus(eBonus, false, bIgnoreFeature, true);
	}

	bool removingVegetationMakesBonusValid(CvPlot const& kPlot, BonusTypes eBonus)
	{
		return (kPlot.isFeature() &&
				GC.getInfo(kPlot.getFeatureType()).getGrowthProbability() > 5 &&
				canHaveBonus(kPlot, eBonus, true));
	}

	CvPlot* findValidBonusSwapDest(CvPlot& kOriginalDest, CvPlot const& kSource)
	{
		BonusTypes const eBonus = kSource.getBonusType();
		if (canHaveBonus(kOriginalDest, eBonus))
			return &kOriginalDest;
		if (removingVegetationMakesBonusValid(kOriginalDest, eBonus))
			return &kOriginalDest;
		for (int iPass = 0; iPass < 2; iPass++)
		{
			bool const bRemoveVegetation = (iPass == 1);
			FOR_EACH_ADJ_PLOT_VAR_RAND(kOriginalDest, mapRand())
			{
				if (pAdj->isWater() != kOriginalDest.isWater() || // save time
					pAdj->getBonusType() != NO_BONUS ||
					pAdj->isImproved()) // goody hut
				{
					continue;
				}
				bool bValid = true;
				for (PlayerIter<CIV_ALIVE> itPlayer;
					bValid && itPlayer.hasNext(); ++itPlayer)
				{
					if (itPlayer->getStartingPlot() == pAdj)
						bValid = false;
				}
				if (!bValid)
					continue;
				if (!bRemoveVegetation ? canHaveBonus(*pAdj, eBonus) :
					removingVegetationMakesBonusValid(*pAdj, eBonus))
				{
					return pAdj;
				}
			}
		}
		return NULL;
	}
}


void TrueStarts::setPlayerWeightsPerPlot(PlotNumTypes ePlot,
	EagerEnumMap<PlayerTypes,scaled>& kPlayerWeights) const
{
	for (PlayerIter<CIV_ALIVE> itPlayer; itPlayer.hasNext(); ++itPlayer)
	{
		kPlayerWeights.set(itPlayer->getID(),
				m_plotWeights.get(itPlayer->getID(), ePlot));
	}
}


void TrueStarts::sanitize()
{
	CvMap const& kMap = GC.getMap();
	std::vector<std::pair<scaled,PlotNumTypes> > areFitnessPerBonusPlot;
	FOR_EACH_ENUM_RAND(PlotNum, mapRand()) // Will frequently tie at 0 fitness
	{
		CvPlot const& kPlot = kMap.getPlotByIndex(eLoopPlotNum);
		if (kPlot.getBonusType() != NO_BONUS)
		{
			EagerEnumMap<PlayerTypes,scaled> aerPlayerWeights;
			setPlayerWeightsPerPlot(eLoopPlotNum, aerPlayerWeights);
			scaled rFitness = calcBonusFitness(kPlot, aerPlayerWeights);
			areFitnessPerBonusPlot.push_back(std::make_pair(rFitness, eLoopPlotNum));
		}
	}
	// Consider swapping pairs of bonus plots with subpar fitness values
	std::sort(areFitnessPerBonusPlot.begin(), areFitnessPerBonusPlot.end());
	{
		bool bLog = true;
		IFLOG
		{
			int iNegativeFitPlots = 0;
			for (size_t i = 0; i < areFitnessPerBonusPlot.size(); i++)
			{
				if (areFitnessPerBonusPlot[i].first < 0)
					iNegativeFitPlots++;
			}
			logBBAI("%d plots with negative bonus fitness value", iNegativeFitPlots);
		}
	}
	std::set<CvPlot*> apSwappedPlots; // Swap each bonus resource at most once
	/*	Yep, this variable name doesn't bode well. Perhaps the inner loop should
		just always go through all resource plots. I think the current implementation
		mostly saves time - by picking the best match only from among the first third
		or so of the vector unless no valid match is found there at all. Well, this
		also ensures that two problematic resources are dealt with in a single swap
		whenever that's possible. Then again, calcBonusSwapUtil would probably
		prefer such swaps even if swaps with unproblematic resources were
		considered right away ... */
	int iContinueInnerLoopAt = -1;
	scaled const rNeverSwapThresh = fixp(0.4);
	for (size_t i = 0; 3 * i < areFitnessPerBonusPlot.size() &&
		areFitnessPerBonusPlot[i].first < 0; i++)
	{
		CvPlot& kFirstPlot = kMap.getPlotByIndex(areFitnessPerBonusPlot[i].second);
		if (apSwappedPlots.count(&kFirstPlot) > 0)
			continue;
		scaled rMaxUtil;
		CvPlot* pBestPlot = NULL;
		int j;
		for (j = std::max<int>(i + 1, iContinueInnerLoopAt);
			areFitnessPerBonusPlot[j].first <= rNeverSwapThresh &&
			(iContinueInnerLoopAt >= 0 ?
			j < (int)areFitnessPerBonusPlot.size() :
			(2 * j < (int)areFitnessPerBonusPlot.size() &&
			(areFitnessPerBonusPlot[j].first <= 0 ||
			3 * j < (int)areFitnessPerBonusPlot.size()))); j++)
		{
			CvPlot& kSecondPlot = kMap.getPlotByIndex(areFitnessPerBonusPlot[j].second);
			if (apSwappedPlots.count(&kSecondPlot) > 0)
				continue;
			scaled rUtil = calcBonusSwapUtil(kFirstPlot, kSecondPlot,
					areFitnessPerBonusPlot[i].first, areFitnessPerBonusPlot[j].first);
			if (rUtil > rMaxUtil)
			{
				rMaxUtil = rUtil;
				pBestPlot = &kSecondPlot;
			}
		}
		bool bLog = true;
		if (pBestPlot == NULL)
		{
			IFLOG
			{
				logBBAI("No bonus resource found to swap with %S (%d,%d)",
						GC.getInfo(kFirstPlot.getBonusType()).getDescription(),
						kFirstPlot.getX(), kFirstPlot.getY());
				if (iContinueInnerLoopAt >= 0)
				{
					logBBAI("Breakdown of fitness calculation ...");
					// Re-calc fitness value with logging enabled
					EagerEnumMap<PlayerTypes,scaled> aerPlayerWeights;
					setPlayerWeightsPerPlot(kFirstPlot.plotNum(), aerPlayerWeights);
					calcBonusFitness(kFirstPlot, aerPlayerWeights, NO_BONUS, true);
					logBBAI("\n");
				}
			}
			if (iContinueInnerLoopAt < 0 && j + 1 < (int)areFitnessPerBonusPlot.size() &&
				areFitnessPerBonusPlot[j + 1].first <= rNeverSwapThresh)
			{
				iContinueInnerLoopAt = j + 1;
				IFLOG logBBAI("Checking resources not previously considered ...");
				i--;
			}
			else iContinueInnerLoopAt = -1;
			continue;
		}
		iContinueInnerLoopAt = -1;
		// (Not going to consider kFirstPlot again anyway)
		apSwappedPlots.insert(pBestPlot);
		CvPlot& kFirstSwapPlot = *findValidBonusSwapDest(kFirstPlot, *pBestPlot);
		CvPlot& kSecondSwapPlot = *findValidBonusSwapDest(*pBestPlot, kFirstPlot);
		IFLOG
		{
			logBBAI("Swapping bonus resources %S (%d,%d) and %S (%d,%d)",
					GC.getInfo(kFirstPlot.getBonusType()).getDescription(),
					kFirstPlot.getX(), kFirstPlot.getY(),
					GC.getInfo(pBestPlot->getBonusType()).getDescription(),
					pBestPlot->getX(), pBestPlot->getY());
			if (!canHaveBonus(kFirstSwapPlot, pBestPlot->getBonusType()))
			{
				logBBAI("Removing feature %S from (%d,%d)",
						!kFirstSwapPlot.isFeature() ? L"none(!)" :
						GC.getInfo(kFirstSwapPlot.getFeatureType()).getDescription(),
						kFirstSwapPlot.getX(), kFirstSwapPlot.getY());
			}
			if (!canHaveBonus(kSecondSwapPlot, kFirstPlot.getBonusType()))
			{
				logBBAI("Removing feature %S from (%d,%d)", !kSecondSwapPlot.isFeature() ?
						L"none(!)" : GC.getInfo(kSecondSwapPlot.getFeatureType()).getDescription(),
						kSecondSwapPlot.getX(),kSecondSwapPlot.getY());
			}
			if (&kFirstSwapPlot != &kFirstPlot)
			{
				logBBAI("Moving %S to adj. destination (%d,%d)",
						GC.getInfo(pBestPlot->getBonusType()).getDescription(),
						kFirstSwapPlot.getX(), kFirstSwapPlot.getY());
			}
			if (&kSecondSwapPlot != pBestPlot)
			{
				logBBAI("Moving %S to adj. destination (%d,%d)",
						GC.getInfo(kFirstPlot.getBonusType()).getDescription(),
						kSecondSwapPlot.getX(), kSecondSwapPlot.getY());
			}
			// Re-calc fitness, utility values with logging enabled
			logBBAI("Breakdown of fitness calculations ...");
			EagerEnumMap<PlayerTypes,scaled> aerPlayerWeights;
			setPlayerWeightsPerPlot(kFirstPlot.plotNum(), aerPlayerWeights);
			scaled rFirstVal = calcBonusFitness(
					kFirstPlot, aerPlayerWeights, NO_BONUS, true);
			setPlayerWeightsPerPlot(pBestPlot->plotNum(), aerPlayerWeights);
			scaled rSecondVal = calcBonusFitness(
					*pBestPlot, aerPlayerWeights, NO_BONUS, true);
			logBBAI("Breakdown of swap utility calculation ...");
			scaled rUtil = calcBonusSwapUtil(kFirstPlot, *pBestPlot,
					rFirstVal, rSecondVal, true);
			logBBAI("Swap utility is %d/100\n\n", rUtil.getPercent());
		}
		BonusTypes eFirstOriginalBonus = kFirstPlot.getBonusType();
		kFirstPlot.setBonusType(NO_BONUS);
		if (!canHaveBonus(kFirstSwapPlot, pBestPlot->getBonusType()))
		{
			FAssert(canHaveBonus(kFirstSwapPlot, pBestPlot->getBonusType(), true));
			kFirstSwapPlot.setFeatureType(NO_FEATURE);
		}
		kFirstSwapPlot.setBonusType(pBestPlot->getBonusType());
		pBestPlot->setBonusType(NO_BONUS);
		if (!canHaveBonus(kSecondSwapPlot, eFirstOriginalBonus))
		{
			FAssert(canHaveBonus(kSecondSwapPlot, eFirstOriginalBonus, true));
			kSecondSwapPlot.setFeatureType(NO_FEATURE);
		}
		kSecondSwapPlot.setBonusType(eFirstOriginalBonus);
	}
}


void TrueStarts::initContemporaries()
{
	/*	Precompute a list of contemporary leaders for every leader,
		and also store the time differences for those pairs of leaders
		and, for each leader, the maximum over all time differences
		from contemporary leaders. */
	m_contemporaries.reset();
	m_maxTimeDiff.reset();
	// All leaders for which start-of-reign data is available
	std::vector<LeaderHeadTypes> aeLeaders;
	{
		EagerEnumMap<LeaderHeadTypes,bool> aeAdded; // Just to skip duplicates
		// Cover all potentially valid leaders, i.e. also those not playable by the AI.
		for (size_t i = 0; i < m_validHumanCivs.size(); i++)
		{
			LeaderHeadTypes const eLoopLeader = m_validHumanCivs[i].second;
			if (m_truLeaders.get(eLoopLeader) == NULL ||
				m_truLeaders.get(eLoopLeader)->get(
				CvTruLeaderInfo::StartOfReign) == MIN_INT ||
				aeAdded.get(eLoopLeader))
			{
				continue;
			}
			aeAdded.set(eLoopLeader, true);
			aeLeaders.push_back(eLoopLeader);
		}
	}
	for (size_t i = 0; i < aeLeaders.size(); i++)
	{
		LeaderHeadTypes const eFirst = aeLeaders[i];
		int const iFirstStartOfReign = m_truLeaders.get(eFirst)->get(
				CvTruLeaderInfo::StartOfReign);
		std::vector<std::pair<int,LeaderHeadTypes> > aeiTimeDiffPerOther;
		for (size_t j = 0; j < aeLeaders.size(); j++)
		{
			LeaderHeadTypes const eSecond = aeLeaders[j];
			if (eFirst == eSecond)
				continue;
			int iSecondStartOfReign = m_truLeaders.get(eSecond)->get(
					CvTruLeaderInfo::StartOfReign);
			int iDeltaYears = abs(iFirstStartOfReign - iSecondStartOfReign);
			aeiTimeDiffPerOther.push_back(std::make_pair(
					iDeltaYears, eSecond));
		}
		std::sort(aeiTimeDiffPerOther.begin(), aeiTimeDiffPerOther.end());
		int const iMaxContemporaries = 6;
		int iContemporaries = 0;
		for (size_t j = 0; j < aeiTimeDiffPerOther.size(); j++)
		{
			/*	The iMaxContemporaries nearest leaders are considered (somewhat)
				contemporary. If further leaders are still very close together
				(not going to be the case with the BtS leaders), then those also
				count as contemporary. By picking a constant number of nearest
				leaders, a stricter notion for contemporality applies for periods
				that the game covers in some detail, like the Classical era. */
			if (aeiTimeDiffPerOther[j].first < 25 ||
				iContemporaries < iMaxContemporaries)
			{
				iContemporaries++;
				int iTimeDiff = aeiTimeDiffPerOther[j].first;
				m_contemporaries.set(eFirst,
						aeiTimeDiffPerOther[j].second, iTimeDiff);
				m_maxTimeDiff.set(eFirst,
						std::max(m_maxTimeDiff.get(eFirst), iTimeDiff));
			}
		}
	}
}


bool TrueStarts::isTruBonusDiscouraged(CvTruBonusInfo const* pTruBonus,
	CivilizationTypes eCiv) const
{
	if (pTruBonus == NULL)
		return false;
	CvTruCivInfo const* pTruCiv = m_truCivs.get(eCiv);
	EraTypes aeUntil[] = {
			pTruCiv == NULL || pTruCiv->getGeoRegion() == NO_ARTSTYLE ? (EraTypes)0 :
			pTruBonus->getRegionDiscouragedUntil(pTruCiv->getGeoRegion()),
			pTruBonus->getCivDiscouragedUntil(eCiv),
	};
	for (int i = 0; i < ARRAYSIZE(aeUntil); i++)
	{
		if (aeUntil[i] == NO_ERA || aeUntil[i] > GC.getGame().getStartEra())
			return true;
	}
	return false;
}


bool TrueStarts::isTruBonusEncouraged(CvTruBonusInfo const* pTruBonus,
	CivilizationTypes eCiv) const
{
	if (pTruBonus == NULL)
		return false;
	EraTypes eUntil = pTruBonus->getCivEncouragedUntil(eCiv);
	return (eUntil == NO_ERA || eUntil > GC.getGame().getStartEra());
}


CvTruBonusInfo const* TrueStarts::getTruBonus(CvPlot const& kPlot,
	BonusTypes eBonus) const
{
	if (eBonus == NO_BONUS)
		eBonus = kPlot.getBonusType();
	if (eBonus == NO_BONUS)
		return NULL;
	CvTruBonusInfo const* pTruBonus = m_truBonuses.get(eBonus);
	if (pTruBonus == NULL)
		return NULL;
	if (pTruBonus->get(CvTruBonusInfo::LandOnly) && kPlot.isWater())
		return NULL;
	return pTruBonus;
}


void TrueStarts::changeCivs()
{
	m_civs.reset();
	m_leaders.reset();
	m_civTaken.reset();
	m_leaderTaken.reset();

	{
		std::vector<CivilizationTypes> aeValidHumanCivs;
		std::vector<CivilizationTypes> aeValidAICivs;
		m_validHumanCivs.clear();
		m_validAICivs.clear();
		// (Unnecessary performance tweak ...)
		aeValidHumanCivs.reserve(GC.getNumCivilizationInfos());
		aeValidAICivs.reserve(GC.getNumCivilizationInfos());
		m_validHumanCivs.reserve(GC.getNumLeaderHeadInfos());
		m_validAICivs.reserve(GC.getNumLeaderHeadInfos());
		// Randomize to avoid persistent biases when fitness values are tied
		FOR_EACH_ENUM_RAND(Civilization, syncRand())
		{
			CvCivilizationInfo const& kLoopCiv = GC.getInfo(eLoopCivilization);
			if (kLoopCiv.isPlayable())
				aeValidHumanCivs.push_back(eLoopCivilization);
			if (kLoopCiv.isAIPlayable())
				aeValidAICivs.push_back(eLoopCivilization);
		}
		FOR_EACH_ENUM_RAND(LeaderHead, syncRand())
		{
			for (size_t i = 0; i < aeValidAICivs.size(); i++)
			{
				if (GC.getInfo(aeValidAICivs[i]).isLeaders(eLoopLeaderHead))
				{
					m_validAICivs.push_back(std::make_pair(
							aeValidAICivs[i], eLoopLeaderHead));
				}
			}
			for (size_t i = 0; i < aeValidHumanCivs.size(); i++)
			{
				if (GC.getInfo(aeValidHumanCivs[i]).isLeaders(eLoopLeaderHead))
				{
					m_validHumanCivs.push_back(std::make_pair(
							aeValidHumanCivs[i], eLoopLeaderHead));
				}
			}
		}
	}
	// Could do this in ctor, but I want to use the valid-civ lists above.
	initContemporaries();
	{
		std::vector<scaled> arOceanityTargets;
		for (size_t i = 0; i < m_validAICivs.size(); i++)
		{
			CvTruCivInfo const& kTruCiv = *m_truCivs.get(m_validAICivs[i].first);
			scaled rSample = per100(kTruCiv.get(
					CvTruCivInfo::Oceanity));
			if (rSample >= 0)
				arOceanityTargets.push_back(rSample);
			m_iMaxMaxElevationTarget = std::max(m_iMaxMaxElevationTarget,
					kTruCiv.get(CvTruCivInfo::MaxElevation));
		}
		if (!arOceanityTargets.empty())
			m_rMedianOceanityTarget = stats::median(arOceanityTargets);
	}
	updateFitnessValues();

	std::vector<std::pair<int,PlayerTypes> > aiePriorityPerPlayer;
	for (PlayerIter<CIV_ALIVE> itPlayer; itPlayer.hasNext(); ++itPlayer)
	{
		int iBestFitVal = MIN_INT;
		std::vector<std::pair<CivilizationTypes,LeaderHeadTypes> > const& validCivs =
				(itPlayer->isHuman() ? m_validHumanCivs : m_validAICivs);
		for (size_t i = 0; i < validCivs.size(); i++)
		{
			iBestFitVal = std::max(iBestFitVal,
					m_fitnessVals.at(itPlayer->getID()).
					get(validCivs[i].first, validCivs[i].second));
		}
		// Starts with the most difficult player (worst fit)
		int iPriority = -iBestFitVal;
		// Prioritize humans even more
		if (itPlayer->isHuman())
			iPriority += 1000;
		aiePriorityPerPlayer.push_back(std::make_pair(
				iPriority, itPlayer->getID()));
	}
	std::sort(aiePriorityPerPlayer.rbegin(), aiePriorityPerPlayer.rend());
	for (size_t i = 0; i < aiePriorityPerPlayer.size(); i++)
	{
		PlayerTypes const ePlayer = aiePriorityPerPlayer[i].second;
		if (m_leaders.get(ePlayer) != NO_LEADER)
			continue;

		bool bLog = true;
		std::pair<CivilizationTypes,LeaderHeadTypes> ee2ndBestFit(
				NO_CIVILIZATION, NO_LEADER);
		int i2ndBestFitVal = MIN_INT;

		std::pair<CivilizationTypes,LeaderHeadTypes> eeBestFit(
				NO_CIVILIZATION, NO_LEADER);
		int iBestFitVal = MIN_INT;
		std::vector<std::pair<CivilizationTypes,LeaderHeadTypes> > const& validCivs =
				(GET_PLAYER(ePlayer).isHuman() ? m_validHumanCivs : m_validAICivs);
		for (size_t j = 0; j < validCivs.size(); j++)
		{
			if (m_leaderTaken.get(validCivs[j].second) ||
				m_civTaken.get(validCivs[j].first))
			{
				continue;
			}
			int iFitVal = m_fitnessVals.at(ePlayer).get(
					validCivs[j].first, validCivs[j].second);
			if (iFitVal > iBestFitVal)
			{
				iBestFitVal = std::max(iBestFitVal, iFitVal);
				eeBestFit = validCivs[j];
			}
			else
			{
				IFLOG
				{
					if (iFitVal > i2ndBestFitVal &&
						// Different leader of same civ isn't going to be interesting
						validCivs[j].first != eeBestFit.first)
					{
						i2ndBestFitVal = std::max(i2ndBestFitVal, iFitVal);
						ee2ndBestFit = validCivs[j];
					}
				}
			}
		}
		if (eeBestFit.first != NO_CIVILIZATION &&
			eeBestFit.second != NO_LEADER)
		{
			IFLOG // Recalc w/ log output
			{
				calcFitness(GET_PLAYER(ePlayer),
						eeBestFit.first, eeBestFit.second, true);
				// Also break down calculation for second best fit
				if (ee2ndBestFit.first != NO_CIVILIZATION &&
					ee2ndBestFit.second != NO_LEADER)
				{
					logBBAI("Best alternative to %S:", GC.getInfo(eeBestFit.first).getShortDescription());
					calcFitness(GET_PLAYER(ePlayer),
							ee2ndBestFit.first, ee2ndBestFit.second, true);
				}
				/*	For logging a particular leader that perhaps should've been
					chosen instead. (Only makes sense with fixed seeds I think.) */
				/*LeaderHeadTypes eLeader = (LeaderHeadTypes)
						GC.getInfoTypeForString("LEADER_");
				CivilizationTypes eLeaderCiv = NO_CIVILIZATION;
				FOR_EACH_ENUM(Civilization)
				{
					if (GC.getInfo(eLoopCivilization).isLeaders(eLeader))
					{
						eLeaderCiv = eLoopCivilization;
						break;
					}
				}
				if (eLeaderCiv != NO_CIVILIZATION)
				{
					logBBAI("For comparison: Fitness eval for %S", GC.getInfo(eLeader).getDescription());
					calcFitness(GET_PLAYER(ePlayer), eLeaderCiv, eLeader, true);
				}
				else FErrorMsg("No civ found for eLeader");*/
			}
			if (GC.getGame().isOption(GAMEOPTION_LEAD_ANY_CIV))
			{
				/*	When leaders are unrestricted, then the best-fit has been
					selected only based on a civ. Stick to that civ, and
					combine it with a random leader. */
				std::vector<LeaderHeadTypes> aeAvailableLeaders;
				for (size_t j = 0; j < validCivs.size(); j++)
				{
					if (!m_leaderTaken.get(validCivs[j].second))
						aeAvailableLeaders.push_back(validCivs[j].second);
				}
				if (!aeAvailableLeaders.empty())
				{
					eeBestFit.second = aeAvailableLeaders[SyncRandNum(
							aeAvailableLeaders.size())];
				}
				else FErrorMsg("At least eeBestFit.second should be available");
			}
			m_civs.set(ePlayer, eeBestFit.first);
			m_leaders.set(ePlayer, eeBestFit.second);
			m_civTaken.set(eeBestFit.first, true);
			m_leaderTaken.set(eeBestFit.second, true);
			// To avoid assigning alternative colors in the loop below
			GC.getInitCore().setColor((PlayerTypes)ePlayer, NO_PLAYERCOLOR);
		}
		/*	Recalculate each time that we lock a player in. (Could skip the players
			that we're already done with, but I don't think performance matters
			much here.) */
		updateFitnessValues();
	}
	for (PlayerIter<CIV_ALIVE> itPlayer; itPlayer.hasNext(); ++itPlayer)
	{
		CivilizationTypes const eCiv = m_civs.get(itPlayer->getID());
		LeaderHeadTypes const eLeader = m_leaders.get(itPlayer->getID());
		if (eCiv == NO_CIVILIZATION)
		{
			FErrorMsg("No civ found for player");
			continue;
		}
		if (eLeader == NO_LEADER)
		{
			FErrorMsg("No leader found for player");
			continue;
		}
		/*	bChangeDescr param:
			Non-scenario games leave all civ and leader names empty,
			which means that CvInfo descriptions get used. That's fine, but
			the hardwired names in scenarios need to be changed explicitly. */
		itPlayer->changeCiv(eCiv, GC.getGame().isScenario(), true);
		itPlayer->changeLeader(eLeader, GC.getGame().isScenario());
	}
}


void TrueStarts::calculateRadius(CvPlayer const& kPlayer)
{
	CvMap const& kMap = GC.getMap();
	scaled rRadius = 6 + kMap.getWorldSize();
	{
		scaled rCrowdedness(PlayerIter<CIV_ALIVE>::count(),
				GC.getGame().getRecommendedPlayers());
		if (rCrowdedness > 1)
			rRadius /= rCrowdedness.sqrt();
		else rRadius += 2 / rCrowdedness - 1;
	}
	// Increase radius when there's a lot of ocean in surrounding plots
	int iExtra = 0;
	scaled const rTargetNonOcean = fixp(2.25) * SQR(rRadius);
	CvPlot const& kStart = *kPlayer.getStartingPlot();
	do
	{
		int iNonOcean = 0;
		for (PlotCircleIter itPlot(kStart, rRadius.round() + iExtra);
			itPlot.hasNext(); ++itPlot)
		{
			if (sameArea(*itPlot, kStart) ||
				(itPlot->getTerrainType() == GC.getWATER_TERRAIN(true) &&
				itPlot->isAdjacentToArea(kStart.getArea())))
			{
				/*	Would be nice not to count plots fully that are close to
					another starting plot (tbd.?) */
				iNonOcean++;
			}
		}
		if (iNonOcean >= rTargetNonOcean)
			break;
		iExtra++;
	} while (iExtra < fixp(0.4) * rRadius);
	rRadius += iExtra;
	m_radii.set(kPlayer.getID(), rRadius.round());
}


void TrueStarts::updateFitnessValues()
{
	m_fitnessVals.clear();
	m_fitnessVals.resize(NUM_CIV_PLAYER_TYPES);
	for (PlayerIter<CIV_ALIVE> itPlayer; itPlayer.hasNext(); ++itPlayer)
	{
		if (!GC.getInitCore().wasCivRandomlyChosen(itPlayer->getID()) &&
			!GC.getGame().isScenario() &&
			// Can't sync up the was-randomly-chosen info in time
			!GC.getGame().isNetworkMultiPlayer())
		{
			m_civs.set(itPlayer->getID(), itPlayer->getCivilizationType());
			m_leaders.set(itPlayer->getID(), itPlayer->getLeaderType());
			m_civTaken.set(itPlayer->getCivilizationType(), true);
			m_leaderTaken.set(itPlayer->getLeaderType(), true);
			continue;
		}
		std::vector<std::pair<CivilizationTypes,LeaderHeadTypes> > const& validCivs =
				(itPlayer->isHuman() ? m_validHumanCivs : m_validAICivs);
		for (size_t i = 0; i < validCivs.size(); i++)
		{
			m_fitnessVals.at(itPlayer->getID()).set(
					validCivs[i].first, validCivs[i].second,
					calcFitness(*itPlayer, validCivs[i].first, validCivs[i].second));
		}
	}
}


namespace
{
	scaled distWeight(CvPlot const& kStart, CvPlot const& kPlot, int iMaxDist)
	{
		int iPlotDist = plotDistance(&kStart, &kPlot);
		if (!kStart.sameArea(kPlot)) // (Don't use our local sameArea function here)
			iPlotDist *= 2;
		return scaled::max(0, 1 - scaled(iPlotDist, iMaxDist + 1).
				pow(fixp(1.7)));
	}
}


int TrueStarts::calcFitness(CvPlayer const& kPlayer, CivilizationTypes eCiv,
	LeaderHeadTypes eLeader, bool bLog) const
{
	CvPlot const& kStart = *kPlayer.getStartingPlot();
	IFLOG logBBAI("Fitness calc for %S of %S on (%d,%d)",
			GC.getInfo(eLeader).getDescription(), GC.getInfo(eCiv).getShortDescription(),
			kStart.getX(), kStart.getY());
	CvTruCivInfo const& kTruCiv = *m_truCivs.get(eCiv);
	int iFitness = 1000;
	if (m_bMapHasLatitudes)
	{
		int const iAbsStartLat = kStart.getLatitude();
		int iAbsStartLatAdjustedTimes10 = iAbsStartLat * 10;
		/*	Try to match latitudes slightly higher than the actual latitudes -
			to bias the civ choice toward the temperate zones and subtropics. */
		iAbsStartLatAdjustedTimes10 += (scaled(std::max(0,
				40 - iAbsStartLat)).pow(fixp(0.4)) * 10).round();
		// Temperate latitudes need to keep some distance from the Tundra
		iAbsStartLatAdjustedTimes10 -= (scaled(std::max(0,
				std::min(52, iAbsStartLat) - 40)).pow(fixp(0.4)) * 10).round();
		int iAbsLatTimes10 = range(iAbsStartLatAdjustedTimes10, 0, 900);
		int iCivAbsLatTimes10 = abs(kTruCiv.get(CvTruCivInfo::LatitudeTimes10));
		int iError = iCivAbsLatTimes10 - iAbsLatTimes10;
		bool const bStartTooWarm = (iError > 0);
		iError = abs(iError);
		int const iMaxMagnifiedError = 5;
		int iErrorMagnifier = std::max(0, iMaxMagnifiedError -
				/*	Errors near the temperate-subarctic and the subtropic-tropic
					boundaries are especially noticeable */
				(bStartTooWarm ? abs(iAbsStartLat - 20) : abs(iAbsStartLat - 50)));
		iError = std::max(0, iError - iMaxMagnifiedError * 10) + // Not magnified
				(std::min(iError, iMaxMagnifiedError * 10) * // Magnify this portion
				// At most double it
				(100 + (100 * iErrorMagnifier) / iMaxMagnifiedError)) / 100;
		int iLatPenalty = (3 * iError) / 2; // weight
		IFLOG logBBAI("Penalty for latitude %d (start at %d, civ at %d/10)",
				iLatPenalty, iAbsStartLat, abs(kTruCiv.get(CvTruCivInfo::LatitudeTimes10)));
		iFitness -= iLatPenalty;
	}
	{
		CvMap const& kMap = GC.getMap();
		int const iCivLatitudeTimes10 = kTruCiv.get(CvTruCivInfo::LatitudeTimes10);
		int const iCivLongitudeTimes10 = kTruCiv.get(CvTruCivInfo::LongitudeTimes10);
		int iOtherPlayers = 0;
		int iAvgDistErrorPercent = 0;
		FOR_EACH_NON_DEFAULT_PAIR(m_civs, Player, CivilizationTypes)
		{
			if (perPlayerVal.first == kPlayer.getID())
				continue;
			iOtherPlayers++;
			CvTruCivInfo const& kLoopTruCiv = *m_truCivs.get(perPlayerVal.second);
			CvPlot const& kOtherStart = *GET_PLAYER(perPlayerVal.first).getStartingPlot();
			int iDist = kMap.plotDistance(&kOtherStart, &kStart);
			int iMaxDist = GC.getMap().maxPlotDistance();
			int iLoopLatitudeTimes10 = kLoopTruCiv.get(CvTruCivInfo::LatitudeTimes10);
			int iLatitudeDiffTimes10 = abs(iCivLatitudeTimes10 - iLoopLatitudeTimes10);
			int iMaxLatitudeDiffTimes10 = CvTruCivInfo::maxLatitude()
					- CvTruCivInfo::minLatitude();
			if (kMap.isWrapY())
				iLatitudeDiffTimes10 %= iMaxLatitudeDiffTimes10;
			int iLongitudeDiffTimes10 = abs(iCivLongitudeTimes10
					- kLoopTruCiv.get(CvTruCivInfo::LongitudeTimes10));
			int iMaxLongitudeDiffTimes10 = CvTruCivInfo::maxLongitude()
					- CvTruCivInfo::minLongitude();
			if (kMap.isWrapX())
				iLongitudeDiffTimes10 %= iMaxLongitudeDiffTimes10;
			// Let's use the same approximation of Euclidean distance as plotDistance
			int iGeoDist = std::max(iLongitudeDiffTimes10, iLatitudeDiffTimes10)
					+ std::min(iLongitudeDiffTimes10, iLatitudeDiffTimes10) / 2;
			int iMaxGeoDist = kMap.maxPlotDistance(iMaxLongitudeDiffTimes10,
					iMaxLatitudeDiffTimes10);
			int iGeoDistPercent = 100 * iGeoDist / iMaxGeoDist;
			int iDistPercent = 100 * iDist / iMaxDist;
			/*	(Don't need such an adjustment for geo dist - America and Eurasia
				are pretty far apart anyway, and all other relevant places are
				connected by land.) */
			if (!sameArea(kStart, kOtherStart))
				iDistPercent += (18 * (100 - iDistPercent)) / 100;
			int iErrorPercent = abs(iDistPercent - iGeoDistPercent);
			{
				/*	Mean dist value at which the error is given maximal weight.
					Because, if both distances are short or long, it's not so important
					how short or long exactly. Don't need a scale model; mainly want to
					have the right neighbors. */
				int const iMaxErr = 25;
				iErrorPercent *= (iMaxErr + std::max(0, iMaxErr - std::min(
						abs(std::max(iDistPercent, iGeoDistPercent) - iMaxErr),
						abs(std::min(iDistPercent, iGeoDistPercent) - iMaxErr))));
				iErrorPercent /= iMaxErr;
				/*	Avoid placing civs that are close together at the wrong side
					of the equator */
				if (iCivLatitudeTimes10 * iLoopLatitudeTimes10 < 0)
					iErrorPercent = std::max(iErrorPercent, iMaxErr + 5);
			}
			iAvgDistErrorPercent += iErrorPercent;
			IFLOG logBBAI("Dist error for %S: %d percent (plot dist %d percent, geo dist %d percent)",
					GC.getInfo(perPlayerVal.second).getShortDescription(), iErrorPercent, iDistPercent, iGeoDistPercent);
		}
		scaled rAvgDistErrorPenalty = iAvgDistErrorPercent * fixp(0.48);
		if (iOtherPlayers > 0)
		{
			/*	Not quite an average (that would be pow(1)). I do want distances
				to matter more as the last few civs are chosen. */
			rAvgDistErrorPenalty /= scaled(iOtherPlayers).pow(fixp(0.77));
			IFLOG logBBAI("Subtracting %d from fitness for dist error", rAvgDistErrorPenalty.round());
		}
		iFitness -= rAvgDistErrorPenalty.round();
	}
	int const iOurMaxTimeDiff = m_maxTimeDiff.get(eLeader);
	if (iOurMaxTimeDiff >= 0)
	{
		int iFromContemporaries = 0;
		int const iWeight = 36;
		int const iFixed = 14;
		/*	Go through all players already assigned whose leader is
			contemporary with eLeader. We only care which leaders are in
			the game here, not where they're located on the map. */
		FOR_EACH_NON_DEFAULT_PAIR(m_leaders, Player, LeaderHeadTypes)
		{
			if (perPlayerVal.first == kPlayer.getID())
				continue;
			int iTimeDiff = m_contemporaries.get(eLeader, perPlayerVal.second);
			/*	Contemporary relations aren't always symmetrical, If we're
				their contemporary, that's also good. */
			bool bMutuallyContemporary = false;
			int iMaxTimeDiff = iOurMaxTimeDiff;
			if (iTimeDiff < 0)
			{
				iTimeDiff = m_contemporaries.get(perPlayerVal.second, eLeader);
				iMaxTimeDiff = m_maxTimeDiff.get(perPlayerVal.second);
			}
			else
			{
				bMutuallyContemporary = (0 <=
						m_contemporaries.get(perPlayerVal.second, eLeader));
			}
			if (iTimeDiff >= 0)
			{
				FAssert(iTimeDiff <= iMaxTimeDiff);
				int iPlus = (iMaxTimeDiff - iTimeDiff) * iWeight / iMaxTimeDiff;
				if (TEAMID(perPlayerVal.first) == kPlayer.getTeam())
					iPlus *= 2;
				iPlus += iFixed;
				if (bMutuallyContemporary)
					iPlus += iFixed; // add a second time
				else IFLOG logBBAI("Not counted as mutually contemporary");
				iFromContemporaries += iPlus;
				IFLOG logBBAI("Contemporary leader on the map: %S. Time difference is %d years. Adding %d to fitness (to be adjusted to civ count)",
						GC.getInfo(perPlayerVal.second).getDescription(), iTimeDiff, iPlus);
			}
		}
		iFitness += (iFromContemporaries /
				scaled(m_leaders.numNonDefault()).sqrt()).round();
	}
	{	// Evaluation of surrounding plots ...
		auto_ptr<PlotCircleIter> pSurroundings = getSurroundings(kPlayer.getID());
		scaled rSameAreaPlotWeights;
		scaled rDifferentAreaPlotWeights;
		scaled rAreaRiverScore;
		scaled rAreaRiverWeights;
		scaled rAreaHillScore;
		scaled rAreaPeakScore;
		int iTemperateDesertPenalty = 0;
		scaled rFromBonuses;
		scaled rBonusDiscourageFactor = -scaled(3750, std::max(1,
				m_discouragedBonusesTotal.get(eCiv))).sqrt();
		scaled rBonusEncourageFactor = scaled(880, std::max(1,
				m_encouragedBonusesTotal.get(eCiv))).sqrt();
		bool const bSanitize = (GC.getGame().isScenario() ?
				GC.getDefineBOOL(CvGlobals::TRUE_STARTS_SANITIZE_SCENARIOS) :
				GC.getDefineBOOL(CvGlobals::TRUE_STARTS_SANITIZE));
		// Higher coefficients when ill-fitting resources can't be sanitized away
		if (!bSanitize)
		{
			rBonusDiscourageFactor *= 2;
			rBonusEncourageFactor *= 2;
		}
		/*	For the escalating effect of these counts, it's significant
			that the order of plot traversal is a spiral away from the center. */
		EagerEnumMap<BonusTypes,int> aeiEncouragedCount;
		EagerEnumMap<BonusTypes,int> aeiDiscouragedCount;
		for (PlotCircleIter& itPlot = *pSurroundings; itPlot.hasNext(); ++itPlot)
		{
			scaled const rWeight = m_plotWeights.get(
					kPlayer.getID(), itPlot->plotNum());
			if (!itPlot->isLake())
			{
				if (sameArea(*itPlot, kStart))
				{
					rSameAreaPlotWeights += rWeight;
					if (itPlot->isHills())
					{
						rAreaHillScore += rWeight;
						int iOrthAdj = 0;
						FOR_EACH_ORTH_ADJ_PLOT(*itPlot)
						{
							if (pAdj->isHills() || pAdj->isPeak())
							{
								rAreaHillScore += 2 * rWeight / (3 + iOrthAdj);
								iOrthAdj++;
							}
						}
						int iDiagAdj = 0;
						FOR_EACH_DIAG_ADJ_PLOT(*itPlot)
						{
							if (pAdj->isHills() || pAdj->isPeak())
							{
								rAreaHillScore += rWeight / (2 + iOrthAdj + iDiagAdj);
								iDiagAdj++;
							}
						}
					}
					else if (itPlot->isPeak())
					{
						rAreaPeakScore += rWeight;
						FOR_EACH_ORTH_ADJ_PLOT(*itPlot)
						{
							if (pAdj->isPeak())
								rAreaPeakScore += 2 * rWeight / 3;
							if (pAdj->isHills())
								rAreaPeakScore += rWeight / 3;
						}
						FOR_EACH_DIAG_ADJ_PLOT(*itPlot)
						{
							if (pAdj->isPeak())
								rAreaPeakScore += rWeight / 2;
						}
					}
					// Decrease weight for distant plots when it comes to rivers
					scaled rRiverWeight = SQR(rWeight);
					rAreaRiverWeights += rRiverWeight;
					if (itPlot->isRiver())
					{
						rAreaRiverScore += (itPlot->getRiverCrossingCount()
								+ 2) * rRiverWeight; // dilute
					}
					if (itPlot->getTerrainType() == m_eDesert)
					{
						if (itPlot.currPlotDist() == CITY_PLOTS_RADIUS)
							iTemperateDesertPenalty = 65;
						else if (iTemperateDesertPenalty == 0 &&
							itPlot.currPlotDist() == CITY_PLOTS_RADIUS + 1)
						{
							iTemperateDesertPenalty = 40;
						}
					}
				}
				else
				{
					rDifferentAreaPlotWeights += rWeight;
					if (!itPlot->isWater()) // Count land area double
						rDifferentAreaPlotWeights += rWeight;
				}
			}
			BonusTypes const eBonus = itPlot->getBonusType();
			if (eBonus != NO_BONUS)
			{
				if (isBonusDiscouraged(*itPlot, eCiv))
				{
					aeiDiscouragedCount.add(eBonus, 1);
					scaled rVal = rWeight * rBonusDiscourageFactor;
					if (bSanitize) // Multiple bad resources will be difficult to sanitize
						rVal *= scaled(aeiDiscouragedCount.get(eBonus)).pow(fixp(2/3.));
					IFLOG logBBAI("Discouraging %S at %d,%d (dist. factor: %d percent): -%d/100 fitness",
							GC.getInfo(eBonus).getDescription(), itPlot->getX(), itPlot->getY(),
							rWeight.getPercent(), -rVal.getPercent());
					rFromBonuses += rVal;
				}
				else if (isBonusEncouraged(*itPlot, eCiv))
				{
					aeiEncouragedCount.add(eBonus, 1);
					scaled rVal = rWeight * rBonusEncourageFactor /
							// Mainly want to encourage a single instance
							aeiEncouragedCount.get(eBonus);
					IFLOG logBBAI("Encouraging %S at %d,%d (dist. factor: %d percent): +%d/100 fitness",
							GC.getInfo(eBonus).getDescription(), itPlot->getX(), itPlot->getY(),
							rWeight.getPercent(), rVal.getPercent());
					rFromBonuses += rVal;
				}
			}
			/*	Tbd.: Calculate elevation value/fitness.
				Check for major river if that's a preference. */
		}
		IFLOG if(rFromBonuses!=0) logBBAI("Total fitness from bonus resources: %d",
				rFromBonuses.round());
		iFitness += rFromBonuses.round();
		{
			int iFromClimate = calcClimateFitness(kPlayer,
					kTruCiv.get(CvTruCivInfo::Precipitation),
					kTruCiv.get(CvTruCivInfo::ClimateVariation), bLog);
			IFLOG logBBAI("Fitness value from climate: %d", iFromClimate);
			iFitness += iFromClimate;
		}
		{
			int const iAbsLatitudeTargetTimes10 = abs(kTruCiv.get(
					CvTruCivInfo::LatitudeTimes10));
			// The climate fitness val isn't good at discouraging small desert patches
			if (iTemperateDesertPenalty > 0 &&
				/*	With the BtS civ roster, this covers only Europe incl. Turkey
					(but not all of Europe). */
				iAbsLatitudeTargetTimes10 >= 409 &&
				kTruCiv.get(CvTruCivInfo::Oceanity) >= 10)
			{
				if (iAbsLatitudeTargetTimes10 < 415)
					iTemperateDesertPenalty /= 2;
				IFLOG logBBAI("Fitness penalty of %d for desert in starting city radius", iTemperateDesertPenalty);
				iFitness -= iTemperateDesertPenalty;
			}
		}
		{
			scaled const rTargetOceanity = per100(kTruCiv.get(CvTruCivInfo::Oceanity));
			if (rTargetOceanity >= 0)
			{
				scaled rSameAreaRatio = rSameAreaPlotWeights;
				if (rSameAreaPlotWeights > 0)
					rSameAreaRatio /= rSameAreaPlotWeights + rDifferentAreaPlotWeights;
				IFLOG logBBAI("Same-area plot ratio: %d percent", rSameAreaRatio.getPercent());
				// Give typical oceanity targets less impact on fitness
				scaled rOceanityWeight = rTargetOceanity - m_rMedianOceanityTarget;
				/*	Normalize; i.e. if the median is 0.25, then the weight should
					be more sensitive for targets below the median than above. */
				if (rOceanityWeight > 0 && m_rMedianOceanityTarget < 1)
					rOceanityWeight /= 1 - m_rMedianOceanityTarget;
				else if (m_rMedianOceanityTarget > 0)
					rOceanityWeight /= m_rMedianOceanityTarget;
				rOceanityWeight = rOceanityWeight.abs();
				FAssert(rOceanityWeight <= 1);
				rOceanityWeight += fixp(0.5); // dilute
				/*	Reduce weight for high targets b/c we're unlikely to encounter
					that much water on a Civ map */
				rOceanityWeight *= scaled::min(1, fixp(1.5) - rTargetOceanity);
				IFLOG logBBAI("Target ratio: %d percent, weight factor %d percent (median oceanity: %d percent)",
						(1 - rTargetOceanity).getPercent(), rOceanityWeight.getPercent(),
						m_rMedianOceanityTarget.getPercent());
				scaled rFromOceanity = (1 - rSameAreaRatio - rTargetOceanity).abs() * -175 *
						rOceanityWeight;
				IFLOG logBBAI("Fitness penalty from oceanity: %d", -rFromOceanity.round());
				iFitness += rFromOceanity.round();
			}
			else IFLOG logBBAI("No oceanity data available");
		}
		{
			int const iMajorRiverWeight = kTruCiv.get(CvTruCivInfo::MajorRiverWeight);
			if (iMajorRiverWeight != 0 && rAreaRiverWeights > 0)
			{
				scaled rMeanRiverScore = rAreaRiverScore / rAreaRiverWeights;
				bool bNearRiver = kStart.isRiver();
				if (!bNearRiver)
				{
					FOR_EACH_ADJ_PLOT(kStart)
					{
						if (pAdj->isRiver())
						{
							bNearRiver = true;
							break;
						}
					}
				}
				if (!bNearRiver)
				{
					IFLOG logBBAI("No river near starting plot");
					rMeanRiverScore /= 2;
				}
				IFLOG logBBAI("Mean river score per area plot: %d", rMeanRiverScore.getPercent());
				scaled rFromRiver = (SQR(rMeanRiverScore) * fixp(1.1) - 1) * 100;
				rFromRiver.decreaseTo(150);
				if (rFromRiver < 0 && iMajorRiverWeight > 0)
					rFromRiver *= fixp(1.5);
				rFromRiver *= per100(iMajorRiverWeight);
				IFLOG logBBAI("Fitness from major river: %d (civ weight: %d percent)",
						rFromRiver.round(), iMajorRiverWeight);
				iFitness += rFromRiver.round();
			}
		}
		{
			scaled rDiv = scaled::max(rSameAreaPlotWeights, 1);
			rAreaHillScore /= rDiv;
			rAreaPeakScore /= rDiv;
			IFLOG logBBAI("Area hills and peak score: %d, %d",
					rAreaHillScore.getPercent(), rAreaPeakScore.getPercent());
			scaled const rTargetMountainCover = kTruCiv.get(CvTruCivInfo::MountainousArea);
			if (rTargetMountainCover >= 0)
			{
				scaled rMountainCover = 100 * (rAreaHillScore / 2 + rAreaPeakScore);
				scaled rFromMountainCover = (rMountainCover - rTargetMountainCover).
						abs() * -2; // arbitrary weight factor
				iFitness += rFromMountainCover.round();
				IFLOG logBBAI("Fitness penalty from mountainous area: %d (target %d percent, have %d)",
						rFromMountainCover.round(), rTargetMountainCover.round(), rMountainCover.round());
			}
			int iTargetMaxElev = kTruCiv.get(CvTruCivInfo::MaxElevation);
			if (iTargetMaxElev > MIN_INT)
			{
				scaled rMaxElev = (rAreaPeakScore.getPercent() + 8) * 200;
				// Scenarios may have enormous clumps of peaks
				rMaxElev.decreaseTo(m_iMaxMaxElevationTarget);
				scaled rFromMaxElev = (rMaxElev.sqrt() - scaled(iTargetMaxElev).sqrt()).
						abs() * -2; // arbitrary weight factor
				iFitness += rFromMaxElev.round();
				IFLOG logBBAI("Fitness penalty from max. elevation: %d (target %d m, have %d m)",
						rFromMaxElev.round(), iTargetMaxElev, rMaxElev.round());
			}
		}
	}
	/*	Tbd.: Space, shape preferences: based on plot distances to other starting plots
		in the same area, area size. (Shape also reflected by weights above -> calculatePlotWeights,
		but that's not sufficient.) */
	CvTruLeaderInfo const* pTruLeader = m_truLeaders.get(eLeader);
	int const iCivBias = kTruCiv.get(CvTruCivInfo::Bias);
	int const iLeaderBias = (pTruLeader == NULL ? 0 :
			pTruLeader->get(CvTruLeaderInfo::Bias));
	iFitness *= 100 + iCivBias;
	iFitness /= 100;
	iFitness *= 100 + iLeaderBias;
	iFitness /= 100;
	iFitness += iCivBias + iLeaderBias;
	IFLOG if(iCivBias!=0) logBBAI("Bias against %S: %d percent", GC.getInfo(eCiv).getShortDescription(), iCivBias);
	IFLOG if(iLeaderBias!=0) logBBAI("Bias against %S: %d percent", GC.getInfo(eLeader).getDescription(), iLeaderBias);
	IFLOG logBBAI("Bottom line: %d fitness\n\n", iFitness);
	return iFitness;
}


void TrueStarts::calculatePlotWeights(CvPlayer const& kPlayer)
{
	CvPlot const& kStart = *kPlayer.getStartingPlot();
	auto_ptr<PlotCircleIter> pSurroundings = getSurroundings(kPlayer.getID());
	for (PlotCircleIter& itPlot = *pSurroundings; itPlot.hasNext(); ++itPlot)
	{
		scaled const rDistWeight = distWeight(kStart, *itPlot, itPlot.radius());
		scaled rWeight = rDistWeight;
		// Reduce based on rival weights
		for (PlayerIter<CIV_ALIVE> itOther; itOther.hasNext(); ++itOther)
		{
			if (itOther->getID() != kPlayer.getID())
			{
				scaled rOtherDistWeight = distWeight(
						*itOther->getStartingPlot(), *itPlot, itPlot.radius());
				rWeight *= 1 - scaled::max(0, rOtherDistWeight - rDistWeight);
			}
		}
		/*	Initially, I was going to call CvMap::xDistance, yDistance here and
			adjust the weights to the civ's shape preference. However, then the
			weights should also be recomputed (for every player-civ pair) each
			time a civ is placed b/c the weights of neighboring civs interfere
			with each other. This is computationally expensive enough to introduce
			a delay of several seconds on maps with 18 civs and may make
			super-Huge maps a very slow affair. (So I'll be using a cruder mechanism
			for shape preferences instead.) Framework for civ-specific weights
			deleted on 2 Jan 2021. */
		m_plotWeights.set(kPlayer.getID(), itPlot->plotNum(), rWeight);
	}
}


auto_ptr<PlotCircleIter> TrueStarts::getSurroundings(PlayerTypes ePlayer) const
{
	return auto_ptr<PlotCircleIter>(
			new PlotCircleIter(*GET_PLAYER(ePlayer).getStartingPlot(),
			m_radii.get(ePlayer)));
}

class PrecipitationRegion
{
	scaled m_rWeight;
	scaled m_rPrecipitation;
	CvPlot const* m_pCenter; // (Reference would prevent copying)
public:
	PrecipitationRegion(CvPlot const& kCenter, scaled rWeight, scaled rPrecipitation)
	:	m_pCenter(&kCenter), m_rWeight(rWeight), m_rPrecipitation(rPrecipitation)
	{ FAssert(rWeight < 2); } // Make sure the params don't get mixed up
	scaled getWeight() const { return m_rWeight; }
	scaled getPrecipitation() const { return m_rPrecipitation; }
	CvPlot const& getCenter() const { return *m_pCenter; }
};


int TrueStarts::calcClimateFitness(CvPlayer const& kPlayer, int iTargetPrecipitation,
	int iTargetVariation, bool bLog) const
{
	CvPlot const& kStart = *kPlayer.getStartingPlot();
	/*	Computing a weighted mean over the entire surroundings of kStart
		doesn't work well (I've tried); it's usually a muddle. Need to look at
		subregions with more distinct characteristics. I think that's how
		players perceive the map, e.g. "there's a major desert." */
	std::vector<PrecipitationRegion> aRegions;
	int const iDistBetweenRegions = (GC.getMap().getWorldSize() < 2 ? 3 : 4);
	for (PlotCircleIter itCenter(kStart, iDistBetweenRegions);
		itCenter.hasNext(); ++itCenter)
	{
		bool const bStart = (&*itCenter == &kStart);
		// Center the regions on a circle (i.e. on its rim), and one on kStart.
		if (itCenter.currPlotDist() != iDistBetweenRegions && !bStart)
			continue;
		{
			/*	Only consider the 8 plots on a straight orthogonal or
				diagonal line from kStart */
			int iDX = abs(itCenter->getX() - kStart.getX());
			int iDY = abs(itCenter->getY() - kStart.getY());
			if (iDX != 0 && iDY != 0 && iDX != iDY)
				continue;
		}
		std::vector<std::pair<scaled,scaled> > arrRegionData;
		for (CityPlotIter itPlot(*itCenter); itPlot.hasNext(); ++itPlot)
		{
			int iPrecipitation = precipitation(*itPlot, &*itPlot == &kStart);
			if (iPrecipitation < 0)
				continue;
			scaled rWeight = m_plotWeights.get(kPlayer.getID(), itPlot->plotNum());
			// Extra weight for the most prominent characteristics
			if (itPlot->getFeatureType() == m_eWarmForest)
				rWeight *= fixp(4/3.);
			else if (itPlot->getTerrainType() == m_eDesert)
				rWeight *= fixp(5/3.);
			arrRegionData.push_back(std::make_pair(iPrecipitation, rWeight));
		}
		// Discard some outliers
		std::sort(arrRegionData.begin(), arrRegionData.end());
		int const iValidPlots = (int)arrRegionData.size();
		{
			int const iValidThresh = (NUM_CITY_PLOTS * 5) / 7;
			int const iMaxOutliers = 2; // at each end of the list
			int const iOutliers = std::min(iMaxOutliers,
					(iValidPlots - iValidThresh) / 2);
			/*	(This would be easier to read with a std::list and pop_front,
				but sorting lists is expensive. It's still kind of expensive
				with a vector. The region data calculation is -currently-
				the slowest part of the True Starts code. List code replaced
				on 2 Jan 2021.) */
			if (iOutliers > 0)
			{
				for (size_t i = 0; i + iOutliers < arrRegionData.size(); i++)
					arrRegionData[i] = arrRegionData[i + iOutliers];
				for (int i = 0; i < 2 * iOutliers; i++)
					arrRegionData.pop_back();
			}
		}
		scaled rRegionWeight;
		scaled rRegionPrecipitation;
		for (size_t i = 0; i < arrRegionData.size(); i++)
		{
			rRegionPrecipitation += arrRegionData[i].first;
			rRegionWeight += arrRegionData[i].second;
		}
		if (iValidPlots * 2 <= (bStart ? 0 : NUM_CITY_PLOTS) || rRegionWeight <= 0)
		{
			if (bStart)
			{
				FErrorMsg("At least kStart has to be valid");
				return 0;
			}
			continue;
		}
		rRegionPrecipitation /= iValidPlots;
		rRegionWeight /= iValidPlots;
		aRegions.push_back(PrecipitationRegion(
				*itCenter, rRegionWeight, rRegionPrecipitation));
	}
	if (aRegions.empty())
	{
		FErrorMsg("At least the start region should be valid");
		return 0;
	}
	IFLOG
	{
		logBBAI("Climate regions ...");
		for (size_t i = 0; i < aRegions.size(); i++)
		{
			logBBAI("(%d,%d): %d mm, weight %d percent", aRegions[i].getCenter().getX(), aRegions[i].getCenter().getY(),
					aRegions[i].getPrecipitation().round(), aRegions[i].getWeight().getPercent());
		}
	}
	std::vector<scaled> arPrecipitationFactors;
	// The region around kStart is always important
	arPrecipitationFactors.push_back(aRegions[0].getPrecipitation());
	IFLOG logBBAI("Precipitation in region around start: %d", aRegions[0].getPrecipitation().round());
	{
		// Let's also consider a typical region
		std::vector<std::pair<scaled,scaled> > arrRegionData;
		for (size_t i = 1; i < aRegions.size(); i++) // (skip region around kStart)
		{
			arrRegionData.push_back(std::make_pair(
					aRegions[i].getPrecipitation(), aRegions[i].getWeight()));
		}
		if (!arrRegionData.empty())
		{
			scaled rMedianPrecipitation = stats::weightedMedian(arrRegionData);
			arPrecipitationFactors.push_back(rMedianPrecipitation);
			IFLOG logBBAI("Precipitation of median region: %d", rMedianPrecipitation.round());
		}
	}
	/*	Lastly, see if we can find a region that reinforces the impression
		of the region around kStart. */
	{
		scaled rMinError = scaled::MAX;
		int iBestIndex = -1;
		for (size_t i = 1; i < aRegions.size(); i++)
		{
			scaled rError = (1 / aRegions[i].getWeight()) * // Magnify error if weight small
					(aRegions[i].getPrecipitation() - aRegions[0].getPrecipitation()).
					abs();
			if (rError < rMinError)
			{
				rMinError = rError;
				iBestIndex = i;
			}
		}
		if (iBestIndex > 0)
		{
			scaled rSimilarPrecipitation = aRegions[iBestIndex].getPrecipitation();
			arPrecipitationFactors.push_back(rSimilarPrecipitation);
			IFLOG logBBAI("Precipitation in region most akin to start: %d", rSimilarPrecipitation.round());
		}
	}
	scaled rPrecipitation;
	for (size_t i = 0; i < arPrecipitationFactors.size(); i++)
		rPrecipitation += arPrecipitationFactors[i];
	if (!arPrecipitationFactors.empty())
		rPrecipitation /= arPrecipitationFactors.size();
	{	// Not as varied as the real world. Exaggerate any unusual values.
		int const iTypicalPrecipitation = 600;
		scaled rAdjust = std::min((rPrecipitation - iTypicalPrecipitation).abs(),
				rPrecipitation).pow(fixp(0.7));
		if (rPrecipitation < iTypicalPrecipitation)
			rAdjust *= -1;
		IFLOG logBBAI("Adjusting overall precipitation by %d, to exaggerate.", rAdjust.round());
		rPrecipitation += rAdjust;
	}
	IFLOG logBBAI("Overall precipitation: %d", rPrecipitation.round());
	/*	Very unlikely to match extremely low target precipitation (at least on a
		random map, but even the Earth scenarios aren't that dry), shouldn't
		penalize such a mismatch much. */
	scaled const rVeryLowPrecipThresh = scaled::min(100, rPrecipitation);
	scaled rFitness;
	if (iTargetPrecipitation >= 0)
	{
		rFitness -= (rPrecipitation - scaled::max(iTargetPrecipitation,
				rVeryLowPrecipThresh)).abs() / 2 +
				scaled::max(0, rVeryLowPrecipThresh - iTargetPrecipitation) / 4;
		IFLOG logBBAI("%d fitness penalty from target precipitation of %d",
				-rFitness.round(), iTargetPrecipitation);
		if (aRegions.size() > 1)
		{
			int iCloseMatches = 0;
			int iPossibleMatches = 0;
			for (size_t i = (aRegions.size() <= 2 ? 0 : 1); i < aRegions.size(); i++)
			{
				iPossibleMatches++;
				if ((aRegions[i].getPrecipitation()
					- scaled::max(iTargetPrecipitation, rVeryLowPrecipThresh)).abs() * 5 <
					scaled::max(aRegions[i].getPrecipitation(), iTargetPrecipitation))
				{
					iCloseMatches++;
				}
			}
			scaled rFromCloseMatches = 200 * std::min(scaled(iPossibleMatches, 10),
					scaled(scaled(iCloseMatches, iPossibleMatches).sqrt()
					- fixp(1/3.).sqrt()));
			rFitness += rFromCloseMatches;
			IFLOG logBBAI("Adding %d for %d close matches among %d regions",
					rFromCloseMatches.round(), iCloseMatches, iPossibleMatches);
		}
	}
	else IFLOG logBBAI("No precipitation data available");
	if (iTargetVariation >= 0)
	{
		scaled rTotalError;
		int iSamples = 0;
		for (size_t i = 1; i < arPrecipitationFactors.size(); i++)
		{ 
			rTotalError += (arPrecipitationFactors[i]
					- arPrecipitationFactors[0]).abs();
			iSamples++;
		}
		if (arPrecipitationFactors.size() > 1)
		{
			scaled const rMedian = arPrecipitationFactors[1];
			for (size_t i = 1; i < aRegions.size(); i++)
			{
				// Don't want a region full of jungle to dominate the calculation
				scaled const rRegionPrecip = scaled::min(1250,
						aRegions[i].getPrecipitation());
				/*	Square error to emphasize outliers, double to somewhat match the
					scale of the absolute errors counted above. */
				rTotalError += 2 * SQR((rRegionPrecip - rMedian).abs()) /
						std::max(rMedian + rVeryLowPrecipThresh, scaled::epsilon());
				iSamples++;
			}
		}
		scaled rMeanError = rTotalError / iSamples;
		scaled rVariationScore = rMeanError / 345;
		rVariationScore.decreaseTo(1);
		scaled rFromVariation = (iTargetVariation - rVariationScore.getPercent())
				* fixp(1.5);
		if (rFromVariation < 0) // Too much variation is more problematic
			rFromVariation *= fixp(1.78);
		rFromVariation = -rFromVariation.abs();
		rFitness += rFromVariation;
		IFLOG logBBAI("From mismatch in climate variation: %d (score %d percent, target %d percent)",
				rFromVariation.round(), rVariationScore.getPercent(), iTargetVariation);
	}
	else IFLOG logBBAI("No climate variation data available");
	return rFitness.round();
}

// Millimeters annual, -1 if undetermined.
int TrueStarts::precipitation(CvPlot const& kPlot, bool bStart) const
{
	if (kPlot.isWater() || kPlot.isPeak())
		return -1; // Only consider flat land and hills
	FeatureTypes const eFeature = kPlot.getFeatureType();
	TerrainTypes const eTerrain = kPlot.getTerrainType();
	bool bWarmForest = (eFeature == m_eWarmForest);
	/*	Normalization removes Jungle, obscuring high-precipitation starts.
		Compensate for that (or we'll never have starts wet enough for the Maya). */
	if (!bWarmForest && bStart &&
		(eTerrain == m_eWoodland || eTerrain == m_eSteppe))
	{
		FOR_EACH_ADJ_PLOT(kPlot)
		{
			if (pAdj->getFeatureType() == m_eWarmForest)
			{
				bWarmForest = true;
				break;
			}
		}
	}
	if (bWarmForest)
	{
		return (!m_bMapHasLatitudes ? 2000 :
			3000 - 90 * std::min(20, kPlot.getLatitude()));
	}
	if (eTerrain == m_eWoodland)
	{
		if (eFeature == m_eCoolForest)
		{	/*	This calculation is tailored toward Japan and Korea.
				Very wet temperate forest there. */
			int iExtra = 0;
			FOR_EACH_ADJ_PLOT(kPlot)
			{
				if (pAdj->getTerrainType() == kPlot.getTerrainType() &&
					pAdj->getFeatureType() == kPlot.getFeatureType())
				{
					iExtra += 110;
				}
			}
			return 850 + std::min(iExtra, 550);
		}
		return 750;
	}
	if (eTerrain != m_eDesert && eTerrain != m_ePolarDesert)
	{
		if (eFeature == m_eCoolForest)
			return 500; // Taiga, forest steppe
		return 350; // Tundra, steppe
	}
	// I interpret this as the northernmost taiga
	if (eTerrain == m_ePolarDesert && m_eCoolForest)
		return 250;
	// (Polar) desert ...
	int iExtra = 0;
	FOR_EACH_ADJ_PLOT(kPlot)
	{
		if (pAdj->getTerrainType() == kPlot.getTerrainType() &&
			pAdj->getFeatureType() == kPlot.getFeatureType())
		{
			iExtra -= 25;
		}
	}
	return 200 + iExtra;
}

/*	+1 means the best possible fit, -1 the worst.
	All nonnegative values are acceptable, negative values might be worth
	a swap (but not necessarily; that's for calcBonusSwapUtil to decide). */
scaled TrueStarts::calcBonusFitness(CvPlot const& kPlot,
	EagerEnumMap<PlayerTypes,scaled> const& kPlayerWeights,
	BonusTypes eBonus, bool bLog) const
{
	if (eBonus == NO_BONUS)
		eBonus = kPlot.getBonusType();
	scaled rMinPlayerFitness;
	scaled rTotal;
	for (PlayerIter<CIV_ALIVE> itPlayer; itPlayer.hasNext(); ++itPlayer)
	{
		scaled rWeight = kPlayerWeights.get(itPlayer->getID());
		if (rWeight <= 0) // save time
			continue;
		// Try harder to make human starts fit well
		if (itPlayer->isHuman())
			rWeight *= fixp(4/3.);
		IFLOG logBBAI("Fitness weight of %S for %S (%d,%d): %d percent",
				itPlayer->getName(), GC.getInfo(eBonus).getDescription(),
				kPlot.getX(), kPlot.getY(), rWeight.getPercent());
		scaled rPlayerFitness = rWeight *
				calcBonusFitness(kPlot, *itPlayer, eBonus, bLog);
		rTotal += rPlayerFitness;
		rMinPlayerFitness = std::min(rPlayerFitness, rMinPlayerFitness);
	}
	/*	(Adjustment to the player count shouldn't be necessary:
		Larger maps shouldn't have more overlap between starting surroundings
		than smaller maps, and, if they do, more swapping will be appropriate.
		Crowdedness is already taken into account by the player weights. */
	return (rTotal + rMinPlayerFitness) / 2;
}

/*	Same scale as above if we assume that eBonus is right next to kPlayer's
	starting plot. (Distances are the caller's job to evaluate.)
	However, the +1 is so far only a theoretical upper limit - I don't
	want the encouraged resources to have as strong an effect as the
	discouraged ones. */
scaled TrueStarts::calcBonusFitness(CvPlot const& kPlot, CvPlayer const& kPlayer,
	BonusTypes eBonus, bool bLog) const
{
	scaled const rEncouragement =
			(isBonusEncouraged(kPlot, kPlayer.getCivilizationType(), eBonus) ? fixp(0.55) :
			(isBonusDiscouraged(kPlot, kPlayer.getCivilizationType(), eBonus) ? -1 : 0));
	IFLOG if(rEncouragement!=0) logBBAI("Encouragement value of %S (%d,%d) near %S: %d percent",
			GC.getInfo(eBonus).getDescription(), kPlot.getX(), kPlot.getY(),
			kPlayer.getName(), rEncouragement.getPercent());
	return rEncouragement;
}

namespace
{
	EraTypes getTechRevealEra(CvBonusInfo const& kBonus)
	{
		return (kBonus.getTechReveal() == NO_TECH ? NO_ERA :
				GC.getInfo(kBonus.getTechReveal()).getEra());
	}

	int getClassUniqueRange(CvBonusInfo const& kBonus)
	{
		return (kBonus.getBonusClassType() == NO_BONUSCLASS ? 0 :
				GC.getInfo(kBonus.getBonusClassType()).getUniqueRange());
	}

	/*	Counts the bonus resources within a given range, but only counts
		adjacent bonus resources fully, others weighted by distance. */
	scaled sameBonusInRangeScore(CvPlot const& kPlot, CvBonusInfo const& kBonus,
		int iMaxRange, bool bBonusClass = false)
	{
		scaled rScore;
		for (SquareIter itPlot(kPlot, iMaxRange, false); itPlot.hasNext(); ++itPlot)
		{
			if (itPlot->getBonusType() == NO_BONUS)
				continue;
			CvBonusInfo const& kLoopBonus = GC.getInfo(itPlot->getBonusType());
			if (bBonusClass ?
				(kLoopBonus.getBonusClassType() == kBonus.getBonusClassType()) :
				(&kLoopBonus == &kBonus))
			{
				rScore += 1 - scaled(
						2 * std::max(0, itPlot.currPlotDist() - 1), 3 * iMaxRange).
						pow(fixp(1.5));
			}
		}
		return rScore;
	}
}

/*	Utility greater than 0 means that the swap is worth making all in all,
	i.e. taking into account not just fitness values but also the overall
	disturbance to the map, balance, increase in predictability ...
	The specific positive value says how good the swap is (all in all).
	0 or less means that the swap should not be made, won't generally say
	_how_ bad it is. */
scaled TrueStarts::calcBonusSwapUtil(
	CvPlot const& kFirstPlot, CvPlot const& kSecondPlot,
	scaled rFirstFitness, scaled rSecondFitness, bool bLog) const
{
	CvPlot const* pDestOfSecond = findValidBonusSwapDest(
			/*	Doesn't actually change the plot - but may return it as non-const.
				CvMap only contains non-const CvPlot instances, so such casts are safe. */
			const_cast<CvPlot&>(kFirstPlot), kSecondPlot);
	if (pDestOfSecond == NULL)
	{
		FAssert(!bLog); // I intend to log only valid swaps
		return 0;
	}
	CvPlot const* pDestOfFirst = findValidBonusSwapDest(
			const_cast<CvPlot&>(kSecondPlot), kFirstPlot);
	if (pDestOfFirst == NULL)
	{
		FAssert(!bLog);
		return 0;
	}
	EagerEnumMap<PlayerTypes,scaled> aerPlayerWeights;
	setPlayerWeightsPerPlot(pDestOfSecond->plotNum(), aerPlayerWeights);
	scaled rFirstFitnessAfterSwap = calcBonusFitness(
			*pDestOfSecond, aerPlayerWeights, kSecondPlot.getBonusType(), bLog);
	setPlayerWeightsPerPlot(pDestOfFirst->plotNum(), aerPlayerWeights);
	scaled rSecondFitnessAfterSwap = calcBonusFitness(
			*pDestOfFirst, aerPlayerWeights, kFirstPlot.getBonusType(), bLog);
	scaled rUtil = rFirstFitnessAfterSwap + rSecondFitnessAfterSwap
			- rFirstFitness - rSecondFitness;
	{
		scaled rDisturbance = fixp(1/4.) + // Base penalty - ideally don't swap anything
				calcBonusSwapDisturbance(
				*pDestOfFirst, kSecondPlot, kFirstPlot.getBonusType(), bLog) +
				calcBonusSwapDisturbance(
				*pDestOfSecond, kFirstPlot, kSecondPlot.getBonusType(), bLog);
		IFLOG logBBAI("Subtracting %d/100 utility for disturbance of original map",
				rDisturbance.getPercent());
		rUtil -= rDisturbance;
	}
	CvBonusInfo const& kFirstBonus = GC.getInfo(kFirstPlot.getBonusType());
	CvBonusInfo const& kSecondBonus = GC.getInfo(kSecondPlot.getBonusType());
	{	// Try to preserve locality of bonus resource types
		scaled rDistPenalty;
		if (!sameArea(*pDestOfFirst, *pDestOfSecond) &&
			// Don't care if resources bleed onto small continents
			2 * pDestOfFirst->getArea().getNumTiles() > 3 * NUM_CITY_PLOTS &&
			2 * pDestOfSecond->getArea().getNumTiles() > 3 * NUM_CITY_PLOTS)
		{
			if (pDestOfFirst->getArea().getNumBonuses(kFirstPlot.getBonusType()) <= 0 &&
				kFirstBonus.isOneArea())
			{
				rDistPenalty += fixp(0.25);
			}
			if (pDestOfSecond->getArea().getNumBonuses(kSecondPlot.getBonusType()) <= 0 &&
				kSecondBonus.isOneArea())
			{
				rDistPenalty += fixp(0.25);
			}
		}
		scaled rSwapDist(plotDistance(pDestOfFirst, pDestOfSecond),
				GC.getMap().maxPlotDistance());
		if (rSwapDist > fixp(0.2))
			rDistPenalty += fixp(0.05);
		IFLOG if(rDistPenalty!=0) logBBAI("Swap distance penalty: %d/100", rDistPenalty.getPercent());
		rUtil -= rDistPenalty;
	}
	{
		scaled rSameInRangeScore =
				sameBonusInRangeScore(
				*pDestOfFirst, kFirstBonus, kFirstBonus.getUniqueRange()) +
				sameBonusInRangeScore(
				*pDestOfSecond, kSecondBonus, kSecondBonus.getUniqueRange()) +
				(sameBonusInRangeScore(
				*pDestOfFirst, kFirstBonus, getClassUniqueRange(kFirstBonus), true) +
				sameBonusInRangeScore(
				*pDestOfSecond, kSecondBonus, getClassUniqueRange(kSecondBonus), true))
				/ 2;
		rSameInRangeScore /= 2; // weight factor
		IFLOG if(rSameInRangeScore!=0) logBBAI("Penalty for same or similar resources nearby: %d/100",
				rSameInRangeScore.getPercent());
		rUtil -= rSameInRangeScore;
	}
	return rUtil;
}


scaled TrueStarts::calcBonusSwapDisturbance(CvPlot const& kDest,
	CvPlot const& kOriginalDest, BonusTypes eNewBonus, bool bLog) const
{
	BonusTypes eOldBonus = kOriginalDest.getBonusType();
	scaled rDisturbance;
	if (&kDest != &kOriginalDest)
		rDisturbance += fixp(0.1);
	if (kDest.isFeature() && // just to save time
		!canHaveBonus(kDest, eOldBonus))
	{
		rDisturbance += fixp(0.06);
	}
	IFLOG if(rDisturbance!=0)logBBAI("Disturbance from non-resource changes at (%d,%d): %d/100",
			kDest.getX(), kDest.getY(), rDisturbance.getPercent());
	CvBonusInfo const& kOldBonus = GC.getInfo(eOldBonus);
	CvBonusInfo const& kNewBonus = GC.getInfo(eNewBonus);
	/*	Note that the penalties for dissimilar resources get counted twice,
		as this function gets called for both plots that are being swapped. */
	{
		EraTypes const eOldRevealEra = getTechRevealEra(kOldBonus);
		EraTypes const eNewRevealEra = getTechRevealEra(kNewBonus);
		EraTypes const eStartEra = GC.getGame().getStartEra();
		scaled rFromReveal = scaled(abs(std::max(eStartEra, eOldRevealEra)
				- std::max(eStartEra, eNewRevealEra))).sqrt() / 9;
		IFLOG if(rFromReveal!=0) logBBAI(
				"Disturbance from swapping revealed with unrevealed resource (%S for %S): %d/100",
				kNewBonus.getDescription(), kOldBonus.getDescription(), rFromReveal.getPercent());
		rDisturbance += rFromReveal;
	}
	if (kOldBonus.isNormalize() != kNewBonus.isNormalize())
	{
		scaled rFromNormalize = fixp(0.04);
		IFLOG logBBAI(
				"Disturbance from swapping resource suitable for normalization with one unsuitable (%S for %S): %d/100",
				kNewBonus.getDescription(), kOldBonus.getDescription(), rFromNormalize.getPercent());
		rDisturbance += rFromNormalize;
	}
	if (rDisturbance > 0)
	{	// Disturbances near starting plots are worse
		for (PlayerIter<CIV_ALIVE> itPlayer; itPlayer.hasNext(); ++itPlayer)
		{
			rDisturbance *= 1 + SQR(m_plotWeights.get(itPlayer->getID(),
					kDest.plotNum()));
		}
	}
	return rDisturbance;
}
