#pragma once
#ifndef DEFENDER_SELECTOR_H
#define DEFENDER_SELECTOR_H

class CvUnit;
class CvPlot;
struct DefenderFilters;

/*	advco.defr: Main class hierarchy for the defender randomization component.
	Part of the Advanced Combat (working title) mod. */
// Abstract base class
class DefenderSelector
{
public:
	DefenderSelector(CvPlot const& kPlot);
	virtual ~DefenderSelector();
	virtual void uninit();
	virtual void update(); // Update cached data (if any)
	virtual CvUnit* getDefender(PlayerTypes eOwner,
			DefenderFilters& kFilters) const=0;
	// Returning empty apDef means all units are valid!
	virtual void getDefenders(std::vector<CvUnit*>& apDef, // out-param
			PlayerTypes eOwner, DefenderFilters& kFilters) const;

protected:
	CvPlot const& m_kPlot;
};

// Encapsulates the BtS defender selection algorithm: select the best defender
class BestDefenderSelector : public DefenderSelector
{
public:
	BestDefenderSelector(CvPlot const& kPlot);
	~BestDefenderSelector();
	// override
	CvUnit* getDefender(PlayerTypes eOwner, DefenderFilters& kFilters) const;
};

// Selects the best defender from a random set
class RandomizedSelector : public BestDefenderSelector
{
public:
	RandomizedSelector(CvPlot const& kPlot);
	~RandomizedSelector();
	void uninit();
	void update();
	// override
	CvUnit* getDefender(PlayerTypes eOwner, DefenderFilters& kFilters) const;
	// override
	void getDefenders(std::vector<CvUnit*>& apDef,
			PlayerTypes eOwner, DefenderFilters& kFilters) const;
	static int maxAvailableDefenders();

protected:
	class Cache
	{
	public:
		Cache();
		void setValid(bool b);
		void clear(int iReserve = -1);
		bool isValid() const;
		IDInfo at(int iPosition) const;
		int size() const;
		void add(IDInfo id, int iValue);
		void sort();
	protected:
		typedef std::pair<int,IDInfo> CacheEntry;
		bool m_bValid;
		std::vector<CacheEntry> m_entries;
	};
	mutable Cache m_cache;
	void validateCache(PlayerTypes eAttackerOwner) const;
	// The main algorithm; want this outside of the cache class.
	void cacheDefenders(PlayerTypes eAttackerOwner) const;
	int biasValue(CvUnit const& kUnit) const;
	int randomValue(CvUnit const& kUnit, PlayerTypes eAttackerOwner) const;
	bool canCombat(CvUnit const& kDefUnit, DefenderFilters const& param) const;
};

#endif
