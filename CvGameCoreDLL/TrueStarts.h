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
	~TrueStarts();
	void changeCivs();
	void sanitize();

private:
	ClimateTypes m_eTemperateClimate;
	bool m_bEmptyNewWorld;
	bool m_bMapHasLatitudes;
	int m_iMaxGeoDist, m_iMaxLatitudeDiffTimes10, m_iMaxLongitudeDiffTimes10;
	EagerEnumMap<CivilizationTypes,CvTruCivInfo*> m_truCivs;
	EagerEnumMap<LeaderHeadTypes,CvTruLeaderInfo*> m_truLeaders;
	EagerEnumMap<BonusTypes,CvTruBonusInfo*> m_truBonuses;
	EagerEnumMap<CivilizationTypes,int,void*,-1> m_absTargetLatitudeTimes10;
	ArrayEnumMap2D<LeaderHeadTypes,LeaderHeadTypes,int,void*,-1> m_contemporaries;
	ArrayEnumMap2D<PlayerTypes,PlotNumTypes,scaled> m_plotWeights;
	EagerEnumMap<PlayerTypes,int> m_radii;
	class SurroundingsStats
	{
	public:
		SurroundingsStats(CvPlayer const& kPlayer, TrueStarts const& kTruStarts);
		int temperateDesertPenalty() const { return m_iTemperateDesertPenalty; }
		scaled differentAreaPlotWeights() const { return m_rDifferentAreaPlotWeights; }
		scaled areaPlotWeights() const { return m_rAreaPlotWeights; }
		scaled areaSpaceWeights() const { return m_rAreaSpaceWeights; }
		scaled areaXSpaceWeights() const { return m_rAreaXSpaceWeights; }
		scaled areaYSpaceWeights() const { return m_rAreaYSpaceWeights; }
		scaled areaRiverWeights() const { return m_rAreaRiverWeights; }
		scaled areaRiverScore() const { return m_rAreaRiverScore; }
		scaled areaHillScore() const { return m_rAreaHillScore; }
		scaled areaPeakScore() const { return m_rAreaPeakScore; }
	private:
		int m_iTemperateDesertPenalty;
		scaled m_rDifferentAreaPlotWeights;
		scaled m_rAreaPlotWeights;
		scaled m_rAreaSpaceWeights;
		scaled m_rAreaXSpaceWeights;
		scaled m_rAreaYSpaceWeights;
		scaled m_rAreaRiverWeights;
		scaled m_rAreaRiverScore;
		scaled m_rAreaHillScore;
		scaled m_rAreaPeakScore;
	};
	ArrayEnumMap<PlayerTypes,SurroundingsStats*> m_surrStats;
	scaled m_rMedianSpace;
	scaled m_rMedianPeakScore;
	scaled m_rMedianOceanityTarget;
	int m_iMaxMaxElevationTarget; // global max
	EagerEnumMap<LeaderHeadTypes,int,void*,-1> m_maxTimeDiff;
	EagerEnumMap<CivilizationTypes,int> m_discouragedBonusesTotal;
	EagerEnumMap<CivilizationTypes,int> m_encouragedBonusesTotal;
	EagerEnumMap<BonusTypes,scaled> m_bonusDiscouragedRatio;
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
	FeatureTypes m_eWarmForest, m_eCoolForest;
	TerrainTypes m_eWoodland, m_eSteppe, m_eTundra, m_eDesert, m_ePolarDesert;

	void overrideScenarioOptions();
	void initTargetLatitudes();
	void initContemporaries();
	void setPlayerWeightsPerPlot(PlotNumTypes ePlot,
			EagerEnumMap<PlayerTypes,scaled>& kPlayerWeights) const;
	void calculatePlotWeights(CvPlayer const& kPlayer);
	std::auto_ptr<PlotCircleIter> getSurroundings(CvPlayer const& kPlayer) const;
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
	int calcClimateFitness(CvPlayer const& kPlayer, int iTargetPrecipitation,
			int iTargetVariation, bool bLog = false) const;
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
