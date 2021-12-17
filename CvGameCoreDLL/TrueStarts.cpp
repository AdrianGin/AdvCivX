// advc.tsl: New file; see comments in header.

#include "CvGameCoreDLL.h"
#include "TrueStarts.h"
#include "CvMap.h"
#include "CvGamePlay.h"
#include "BBAILog.h"

// To enable, toggle 'false' to 'true' and also toggle gLogBBAI.
#define IFLOG if (gLogBBAI && bLog && false)


TrueStarts::TrueStarts() : m_iAttempts(0)
{
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
				m_contemporaries.set(eFirst, aeiTimeDiffPerOther[j].second, iTimeDiff);
				m_maxTimeDiff.set(eFirst, std::max(m_maxTimeDiff.get(eFirst), iTimeDiff));
			}
		}
	}
}

/*	Returns false when we're unhappy with the civ assignment.
	Caller could then regenerate the map. */
bool TrueStarts::changeCivs()
{
	m_civs.reset();
	m_leaders.reset();
	m_civTaken.reset();
	m_leaderTaken.reset();

	/*	The official non-Earth scenarios set all latitude values to 0.
		Can't work with that. */
	if (GC.getMap().getTopLatitude() <= GC.getMap().getBottomLatitude())
		return true;

	m_iAttempts++; // (Tbd.: Maybe the caller will have to keep this count instead)
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
		}
		if (eeBestFit.first != NO_CIVILIZATION &&
			eeBestFit.second != NO_LEADER)
		{
			{	// Recalc w/ log output
				bool const bLog=true; // (Shouldn't toggle this one)
				IFLOG calcFitness(GET_PLAYER((PlayerTypes)ePlayer),
						eeBestFit.first, eeBestFit.second, true);
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

	/*	Tbd.: Check if the overall fitness values are high enough.
		Or rather, check if we use too many civs with unusual
		latitude values - i.e. civs near the equator. We only have a few of those,
		don't want half of them in every game.
		Become more tolerant as m_iAttempts increases. */
	return true;
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


int TrueStarts::calcFitness(CvPlayer const& kPlayer, CivilizationTypes eCiv,
	LeaderHeadTypes eLeader, bool bLog) const
{
	CvPlot const& kPlot = *kPlayer.getStartingPlot();
	IFLOG logBBAI("Fitness calc for %S of %S on (%d,%d)",
			GC.getInfo(eLeader).getDescription(), GC.getInfo(eCiv).getDescription(), kPlot.getX(), kPlot.getY());
	CvTruCivInfo const& kTruCiv = *m_truCivs.get(eCiv);
	int iFitness = 1000;
	{
		/*	Try to match latitudes slightly higher than the actual latitudes -
			to bias the civ choice toward the temperate zones and subtropics. */
		int iAbsLatTimes10 = std::min(90, kPlot.getLatitude() + 4) * 10;
		int iCivAbsLatTimes10 = abs(kTruCiv.get(CvTruCivInfo::LatitudeTimes10));
		int iLatPenalty = abs(iCivAbsLatTimes10 - iAbsLatTimes10);
		IFLOG logBBAI("Penalty for latitude %d (plot at %d, civ at %d/10)",
				iLatPenalty, kPlot.getLatitude(), kTruCiv.get(CvTruCivInfo::LatitudeTimes10));
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
			int iDist = kMap.plotDistance(GET_PLAYER(perPlayerVal.first).
					getStartingPlot(), &kPlot);
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
					GC.getInfo(perPlayerVal.second).getDescription(), iErrorPercent, iDistPercent, iGeoDistPercent);
		}
		if (iOtherPlayers > 0)
		{
			iAvgDistErrorPercent = (iAvgDistErrorPercent /
					/*	Not quite an average (that would be pow(1)).
						I do want distances to matter more as the last few
						civs are chosen. */
					scaled(iOtherPlayers).pow(fixp(0.77))).round();
			IFLOG logBBAI("Subtracting %d from fitness for dist error", iAvgDistErrorPercent);
		}
		iFitness -= iAvgDistErrorPercent;
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
				int iPlus = iFixed +
						(iMaxTimeDiff - iTimeDiff) * iWeight / iMaxTimeDiff;
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
	//CvTruLeaderInfo const* pTruLeader = m_truLeaders.get(eLeader); // can be NULL!
	IFLOG logBBAI("\n");
	return iFitness;
}
