#pragma once
#ifndef TRUE_STARTS_H
#define TRUE_STARTS_H

class CvPlayer;
class PlotCircleIter;

// advc.tsl: Main class for the True Starts game option
class TrueStarts
{
public:
	TrueStarts();
	void changeCivs();
	void sanitize();

private:
	bool m_bMapHasLatitudes;
	EagerEnumMap<CivilizationTypes,CvTruCivInfo*> m_truCivs;
	EagerEnumMap<LeaderHeadTypes,CvTruLeaderInfo*> m_truLeaders;
	EagerEnumMap<BonusTypes,CvTruBonusInfo*> m_truBonuses;
	ArrayEnumMap2D<LeaderHeadTypes,LeaderHeadTypes,int,void*,-1> m_contemporaries;
	ArrayEnumMap2D<PlayerTypes,CivilizationTypes,int> m_radii;
	scaled m_rMedianOceanity;
	EagerEnumMap<LeaderHeadTypes,int,void*,-1> m_maxTimeDiff;
	EagerEnumMap<CivilizationTypes,int> m_discouragedBonusesTotal;
	EagerEnumMap<CivilizationTypes,int> m_encouragedBonusesTotal;
	/*	Fitness values stored per civ-leader pair. In case that a leader
		is valid for multiple civs. (Does the game really support that?)
		Need those values for each player, hence the surrounding vector. */
	std::vector<
		ArrayEnumMap2D<CivilizationTypes,LeaderHeadTypes,int,void*,MIN_INT>
	> m_fitnessVals;
	EagerEnumMap<PlayerTypes,CivilizationTypes> m_civs;
	EagerEnumMap<PlayerTypes,LeaderHeadTypes> m_leaders;
	EagerEnumMap<CivilizationTypes,bool> m_civTaken;
	EagerEnumMap<LeaderHeadTypes,bool> m_leaderTaken;
	std::vector<std::pair<CivilizationTypes,LeaderHeadTypes> > m_validAICivs;
	std::vector<std::pair<CivilizationTypes,LeaderHeadTypes> > m_validHumanCivs;
	std::vector<ArrayEnumMap<PlotNumTypes,scaled> > m_plotWeightsForSanitization;
	FeatureTypes m_eWarmForest, m_eCoolForest;
	TerrainTypes m_eWoodland, m_eSteppe, m_eTundra, m_eDesert, m_ePolarDesert;

	void initContemporaries();
	void setPlayerWeightsPerPlot(PlotNumTypes ePlot,
			EagerEnumMap<PlayerTypes,scaled>& kPlayerWeights) const;
	void calculatePlotWeights(ArrayEnumMap<PlotNumTypes,scaled>& aerWeights,
			PlayerTypes ePlayer, CivilizationTypes eCiv = NO_CIVILIZATION) const;
	std::auto_ptr<PlotCircleIter> getSurroundings(PlayerTypes ePlayer,
			CivilizationTypes eCiv = NO_CIVILIZATION) const;
	bool isBonusDiscouraged(CvPlot const& kPlot, CivilizationTypes eCiv,
		BonusTypes eBonus = NO_BONUS) const
	{
		return isTruBonusDiscouraged(getTruBonus(kPlot, eBonus), eCiv);
	}
	bool isBonusEncouraged(CvPlot const& kPlot, CivilizationTypes eCiv,
		BonusTypes eBonus = NO_BONUS) const
	{
		return isTruBonusEncouraged(getTruBonus(kPlot, eBonus), eCiv);
	}
	CvTruBonusInfo const* getTruBonus(CvPlot const& kPlot,
			BonusTypes eBonus = NO_BONUS) const;
	bool isTruBonusDiscouraged(CvTruBonusInfo const* pTruBonus,
			CivilizationTypes eCiv) const;
	bool isTruBonusEncouraged(CvTruBonusInfo const* pTruBonus,
			CivilizationTypes eCiv) const;
	void calculateRadius(CvPlayer const& kPlayer);
	void updateFitnessValues();
	int calcFitness(CvPlayer const& kPlayer, CivilizationTypes eCiv,
			LeaderHeadTypes eLeader, bool bLog = false) const;
	int calcClimateFitness(CvPlot const& kStart,
			ArrayEnumMap<PlotNumTypes,scaled> const& kWeights,
			int iTargetPrecipitation, int iTargetVariation,
			bool bLog = false) const;
	int precipitation(CvPlot const& kPlot, bool bStart = false) const;
	scaled calcBonusFitness(CvPlot const& kPlot,
			EagerEnumMap<PlayerTypes,scaled> const& kPlayerWeights,
			BonusTypes eBonus = NO_BONUS, bool bLog = false) const;
	scaled calcBonusFitness(CvPlot const& kPlot, CvPlayer const& kPlayer,
			BonusTypes eBonus, bool bLog = false) const;
	scaled calcBonusSwapUtil(CvPlot const& kFirstPlot, CvPlot const& kSecondPlot,
			scaled rFirstFitness, scaled rSecondFitness, bool bLog = false) const;
	scaled calcBonusSwapDisturbance(CvPlot const& kDest, CvPlot const& kOriginalDest,
			BonusTypes eNewBonus, bool bLog = false) const;
};

#endif
