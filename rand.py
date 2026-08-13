import sys

RANDOM_A    =  (1103515245)
RANDOM_C    =  (12345)

MASK32 = 0xFFFFFFFF
m_uiRandomSeed = int(sys.argv[1]) & MASK32

findNum = 0
count = 0
if( len(sys.argv) > 2):
    findNum = int(sys.argv[2])
    while( m_uiRandomSeed != findNum ):
        count = count + 1
        m_uiRandomSeed = ((RANDOM_A * m_uiRandomSeed) + RANDOM_C) & MASK32
        print( m_uiRandomSeed )
    print("Count:" + str(count))
else:
    for i in range(0,10):
        m_uiRandomSeed = ((RANDOM_A * m_uiRandomSeed) + RANDOM_C) & MASK32
        print( m_uiRandomSeed )



