#pragma once
#ifndef TRUE_STARTS_H
#define TRUE_STARTS_H

class CvPlayer;

// advc.tsl: Main class for the True Starts game option
class TrueStarts
{
public:
	TrueStarts();
	void changeCivs();

private:
	ArrayEnumMap<CivilizationTypes,CvTruCivInfo*> m_truCivs;
	ArrayEnumMap<LeaderHeadTypes,CvTruLeaderInfo*> m_truLeaders;
	ArrayEnumMap<BonusTypes,CvTruBonusInfo*> m_truBonuses;
	ArrayEnumMap2D<LeaderHeadTypes,LeaderHeadTypes,int,void*,-1> m_contemporaries;
	ArrayEnumMap<LeaderHeadTypes,int,void*,-1> m_maxTimeDiff;
	/*	Fitness values stored per civ-leader pair. In case that a leader
		is valid for multiple civs. (Does the game really support that?)
		Need those values for each player, hence the surrounding vector. */
	std::vector<
		ArrayEnumMap2D<CivilizationTypes,LeaderHeadTypes,int,void*,MIN_INT>
	> m_fitnessVals;
	ArrayEnumMap<PlayerTypes,CivilizationTypes> m_civs;
	ArrayEnumMap<PlayerTypes,LeaderHeadTypes> m_leaders;
	ArrayEnumMap<CivilizationTypes,bool> m_civTaken;
	ArrayEnumMap<LeaderHeadTypes,bool> m_leaderTaken;
	std::vector<std::pair<CivilizationTypes,LeaderHeadTypes> > m_validAICivs;
	std::vector<std::pair<CivilizationTypes,LeaderHeadTypes> > m_validHumanCivs;

	void initContemporaries();
	void updateFitnessValues();
	int calcFitness(CvPlayer const& kPlayer, CivilizationTypes eCiv,
			LeaderHeadTypes eLeader, bool bLog = false) const;
};

#endif
