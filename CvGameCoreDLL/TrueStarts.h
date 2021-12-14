#pragma once
#ifndef TRUE_STARTS_H
#define TRUE_STARTS_H

class CvPlayer;

// advc.tsl: Main class for the True Starts game option
class TrueStarts
{
public:
	TrueStarts();
	bool changeCivs();

private:
	ArrayEnumMap<CivilizationTypes,CvTruCivInfo*> m_truCivs;
	ArrayEnumMap2D<CivPlayerTypes,CivilizationTypes,int,void*,MIN_INT> m_fitnessVals;
	ArrayEnumMap<CivPlayerTypes,CivilizationTypes> m_civs;
	ArrayEnumMap<CivilizationTypes,bool> m_civTaken;
	ArrayEnumMap<LeaderHeadTypes,bool> m_leaderTaken;
	int m_iAttempts;

	void updateFitnessValues();
	int calcFitness(CvPlayer const& kPlayer, CivilizationTypes eCiv,
			bool bLog = false) const;
};

#endif
