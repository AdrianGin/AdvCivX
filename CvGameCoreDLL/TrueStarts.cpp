// advc.tsl: New file; see comments in header.

#include "CvGameCoreDLL.h"
#include "TrueStarts.h"
#include "CvMap.h"
#include "CvGamePlay.h"
#include "BBAILog.h"


#define IFLOG if (gLogBBAI && bLog && /* toggle to enable: */ false)


TrueStarts::TrueStarts() : m_iAttempts(0)
{
	FOR_EACH_ENUM(TruCiv)
	{
		m_truCivs.set(GC.getInfo(eLoopTruCiv).getCiv(), &GC.getInfo(eLoopTruCiv));
	}
}

/*	Returns false when we're unhappy with the civ assignment.
	Caller could then regenerate the map. */
bool TrueStarts::changeCivs()
{
	m_fitnessVals.reset();
	m_civs.reset();
	m_civTaken.reset();
	m_leaderTaken.reset();
	m_iAttempts++; // (Tbd.: Maybe the caller will have to keep this count instead)

	updateFitnessValues();

	std::vector<std::pair<int,CivPlayerTypes> > aieBestFitPerPlayer;
	for (PlayerIter<CIV_ALIVE> itPlayer; itPlayer.hasNext(); ++itPlayer)
	{
		CivPlayerTypes const ePlayer = (CivPlayerTypes)itPlayer->getID();
		int iBestFitVal = MIN_INT;
		FOR_EACH_ENUM(Civilization)
		{
			iBestFitVal = std::max(iBestFitVal,
					m_fitnessVals.get(ePlayer, eLoopCivilization));
		}
		aieBestFitPerPlayer.push_back(std::make_pair(iBestFitVal, ePlayer));
	}
	// Greedy assignment starting w/ the toughest (worst fit) player
	std::sort(aieBestFitPerPlayer.begin(), aieBestFitPerPlayer.end());
	for (size_t i = 0; i < aieBestFitPerPlayer.size(); i++)
	{
		CivPlayerTypes const ePlayer = aieBestFitPerPlayer[i].second;
		if (m_civs.get(ePlayer) != NO_CIVILIZATION)
			continue;
		CivilizationTypes eBestFitCiv = NO_CIVILIZATION;
		int iBestFitVal = MIN_INT;
		// Randomize, just in case that there are ties.
		FOR_EACH_ENUM_RAND(Civilization, syncRand())
		{
			if (m_civTaken.get(eLoopCivilization))
				continue;
			int iFitVal = m_fitnessVals.get(ePlayer, eLoopCivilization);
			if (iFitVal > iBestFitVal)
			{
				iBestFitVal = std::max(iBestFitVal, iFitVal);
				eBestFitCiv = eLoopCivilization;
			}
		}
		if (eBestFitCiv != NO_CIVILIZATION)
		{
			m_civs.set(ePlayer, eBestFitCiv);
			m_civTaken.set(eBestFitCiv, true);
			// To avoid assigning alternative colors in the loop below
			GC.getInitCore().setColor((PlayerTypes)ePlayer, NO_PLAYERCOLOR);
			// Recalc w/ log output
			bool const bLog=true; // (Shouldn't toggle this one)
			IFLOG calcFitness(GET_PLAYER((PlayerTypes)ePlayer), eBestFitCiv, true);
		}
		/*	Recalculate each time that we lock a civ in. (Could skip the plots that we
			are already done with, but I don't think performance matters much here.) */
		updateFitnessValues();
	}
	for (PlayerIter<CIV_ALIVE> itPlayer; itPlayer.hasNext(); ++itPlayer)
	{
		CivPlayerTypes const ePlayer = (CivPlayerTypes)itPlayer->getID();
		CivilizationTypes const eCiv = m_civs.get(ePlayer);
		if (m_civs.get(ePlayer) == NO_CIVILIZATION)
		{
			FErrorMsg("No civ found for player");
			continue;
		}
		itPlayer->changeCiv(eCiv, true);
		std::vector<LeaderHeadTypes> aeLeaders;
		FOR_EACH_ENUM2(LeaderHead, eLeader)
		{
			CvLeaderHeadInfo const& kLeader = GC.getInfo(eLeader);
			if (!m_leaderTaken.get(eLeader) &&
				(GC.getGame().isOption(GAMEOPTION_LEAD_ANY_CIV) ||
				GC.getInfo(eCiv).isLeaders(eLeader)))
			{
				aeLeaders.push_back(eLeader);
			}
		}
		if (aeLeaders.size() > 0)
			itPlayer->changeLeader(aeLeaders[SyncRandNum(aeLeaders.size())]);
		m_leaderTaken.set(itPlayer->getLeaderType(), true);
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
	for (PlayerIter<CIV_ALIVE> itPlayer; itPlayer.hasNext(); ++itPlayer)
	{
		CivPlayerTypes const ePlayer = (CivPlayerTypes)itPlayer->getID();
		if (!GC.getInitCore().wasCivRandomlyChosen(itPlayer->getID()))
		{
			m_civs.set(ePlayer, itPlayer->getCivilizationType());
			m_civTaken.set(itPlayer->getCivilizationType(), true);
			m_leaderTaken.set(itPlayer->getLeaderType(), true);
			continue;
		}
		FOR_EACH_ENUM2(Civilization, eCiv)
		{
			CvCivilizationInfo const& kCiv = GC.getInfo(eCiv);
			if (kCiv.isPlayable() &&
				(kCiv.isAIPlayable() || itPlayer->isHuman()) &&
				m_truCivs.get(eCiv) != NULL)
			{
				m_fitnessVals.set(ePlayer, eCiv, calcFitness(*itPlayer, eCiv));
			}
		}
	}
}


int TrueStarts::calcFitness(CvPlayer const& kPlayer, CivilizationTypes eCiv, bool bLog) const
{
	CvPlot const& kPlot = *kPlayer.getStartingPlot();
	IFLOG logBBAI("Fitness calc for %S on (%d,%d)", GC.getInfo(eCiv).getDescription(), kPlot.getX(), kPlot.getY());
	CvTruCivInfo const& kTruCiv = *m_truCivs.get(eCiv);
	int iFitness = 1000;
	{
		/*	Try to match latitudes slightly higher than the actual latitudes -
			to bias the civ choice toward the temperate zones and subtropics. */
		int iAbsLatTimes10 = std::min(90, kPlot.getLatitude() + 4) * 10;
		int iCivAbsLatTimes10 = abs(kTruCiv.get(CvTruCivInfo::iLatitudeTimes10));
		int iLatPenalty = abs(iCivAbsLatTimes10 - iAbsLatTimes10);
		IFLOG logBBAI("Penalty for latitude %d (plot at %d, civ at %d)", iLatPenalty, kPlot.getLatitude(), kTruCiv.get(CvTruCivInfo::iLatitudeTimes10));
		iFitness -= iLatPenalty;
	}
	{
		CvMap const& kMap = GC.getMap();
		int const iCivLatitudeTimes10 = kTruCiv.get(CvTruCivInfo::iLatitudeTimes10);
		int const iCivLongitudeTimes10 = kTruCiv.get(CvTruCivInfo::iLongitudeTimes10);
		int iOtherPlayers = 0;
		int iAvgDistErrorPercent = 0;
		FOR_EACH_NON_DEFAULT_PAIR(m_civs, CivPlayer, CivilizationTypes)
		{
			iOtherPlayers++;
			CvTruCivInfo const& kLoopTruCiv = *m_truCivs.get(perCivPlayerVal.second);
			int iDist = kMap.plotDistance(GET_PLAYER((PlayerTypes)perCivPlayerVal.first).
					getStartingPlot(), &kPlot);
			int iMaxDist = GC.getMap().maxPlotDistance();
			int iLatitudeDiffTimes10 = abs(iCivLatitudeTimes10
					- kLoopTruCiv.get(CvTruCivInfo::iLatitudeTimes10));
			int iMaxLatitudeDiffTimes10 = CvTruCivInfo::maxLatitude()
					- CvTruCivInfo::minLatitude();
			if (kMap.isWrapY())
				iLatitudeDiffTimes10 %= iMaxLatitudeDiffTimes10;
			int iLongitudeDiffTimes10 = abs(iCivLongitudeTimes10
					- kLoopTruCiv.get(CvTruCivInfo::iLongitudeTimes10));
			int iMaxLongitudeDiffTimes10 = CvTruCivInfo::maxLongitude()
					- CvTruCivInfo::minLongitude();
			if (kMap.isWrapX())
				iLongitudeDiffTimes10 %= iMaxLongitudeDiffTimes10;
			// Let's use the same approximation of Euclidean distance as plotDistance
			int iGeoDist = std::max(iLongitudeDiffTimes10, iLatitudeDiffTimes10)
					+ std::min(iLongitudeDiffTimes10, iLatitudeDiffTimes10) / 2;
			int iMaxGeoDist = kMap.maxPlotDistance(iMaxLongitudeDiffTimes10,
					iMaxLatitudeDiffTimes10);
			int iErrorPercent = abs(100 * iGeoDist / iMaxGeoDist
					- 100 * iDist / iMaxDist);
			iAvgDistErrorPercent += iErrorPercent;
		}
		if (iOtherPlayers > 0)
			iAvgDistErrorPercent /= iOtherPlayers;
		iFitness -= iAvgDistErrorPercent;
	}
	return iFitness;
}
