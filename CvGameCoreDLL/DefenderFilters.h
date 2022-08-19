#pragma once

#ifndef DEFENDER_FILTERS_H
#define DEFENDER_FILTERS_H

/*	advc: Parameter lists for CvPlot::getBestDefender and related functions
	are getting too long, need to wrap this into a struct. */
struct DefenderFilters
{
	DefenderFilters(
		PlayerTypes eAttackingPlayer = NO_PLAYER, CvUnit const* pAttacker = NULL,
		bool bTestEnemy = false, bool bTestPotentialEnemy = false,
		bool bTestVisible = false, // advc.028
		/*	advc: New params to allow hasDefender checks.
			advc.089: bTestCanAttack=true by default. */
		bool bTestCanAttack = true, bool bTestAny = false,
		/*	(Ideally, this should be swapped with bTestVisible to stay closer
			to the original code. bTestCanMove had been unused for a while.
			Not going to change this now, too error-prone.) */
		bool bTestCanMove = false)
	:	m_eAttackingPlayer(eAttackingPlayer), m_pAttacker(pAttacker),
		m_bTestEnemy(bTestEnemy), m_bTestPotentialEnemy(bTestPotentialEnemy),
		m_bTestVisible(bTestVisible), // advc.028
		m_bTestCanAttack(bTestCanAttack), m_bTestAny(bTestAny), // advc
		m_bTestCanMove(bTestCanMove)
	{}
	PlayerTypes m_eAttackingPlayer;
	CvUnit const* m_pAttacker;
	bool m_bTestEnemy, m_bTestPotentialEnemy,
		 m_bTestVisible, // advc.028
		 m_bTestCanAttack, m_bTestAny, // advc
		 m_bTestCanMove;
};

#endif
