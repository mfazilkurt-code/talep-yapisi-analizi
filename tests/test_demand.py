import unittest
from io import BytesIO
import sys
from pathlib import Path
import pandas as pd
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from src.demand import read_sales_file, classify_group, classify_all, DataValidationError


def csv_read(s,fill=False):
    return read_sales_file(BytesIO(s.encode('utf-8')), 'test.csv',fill_missing_months=fill)


class DemandTests(unittest.TestCase):
    def test_classification_four_quadrants(self):
        m=pd.date_range('2022-01-01',periods=48,freq='MS')
        cases={
            'Smooth':np.array([10,11,12,9]*12,float),
            'Erratic':np.array([1,90,2,100]*12,float),
            'Intermittent':np.array([10 if i%4==0 else 0 for i in range(48)],float),
            'Lumpy':np.array([1 if i%4==0 and i%8==0 else 100 if i%4==0 else 0 for i in range(48)],float),
        }
        for kind, vals in cases.items():
            g=pd.DataFrame({'Ay':m,'Satis':vals})
            self.assertEqual(classify_group(g,kind).sinif,kind)

    def test_empty_sales_zero(self):
        df,info=csv_read('Malzeme Kodu,Ay,Satis\nA,2024-01,10\nA,2024-02,\nA,2024-03,  \n')
        self.assertEqual(df.Satis.tolist(),[10,0,0]);self.assertEqual(info['bos_hucre'],2)

    def test_negative_rejected(self):
        with self.assertRaisesRegex(DataValidationError,'negatif satış'):
            csv_read('Malzeme Kodu,Ay,Satis\nA,2024-01,-2\n')

    def test_invalid_rejected(self):
        with self.assertRaisesRegex(DataValidationError,'geçersiz satış'):
            csv_read('Malzeme Kodu,Ay,Satis\nA,2024-01,yok\n')

    def test_duplicate_rejected(self):
        with self.assertRaisesRegex(DataValidationError,'birden fazla'):
            csv_read('Malzeme Kodu,Ay,Satis\nA,2024-01,2\nA,2024-01,3\n')

    def test_missing_month_is_different(self):
        input='Malzeme Kodu,Ay,Satis\nA,2024-01,2\nA,2024-03,4\n'
        with self.assertRaisesRegex(DataValidationError,'eksik ay'):
            csv_read(input)
        df,info=csv_read(input,fill=True)
        self.assertEqual(df.Satis.tolist(),[2,0,4]);self.assertEqual(info['eklenen_ay'],1)

    def test_zero_and_one_positive(self):
        m=pd.date_range('2024-01-01',periods=6,freq='MS')
        df=pd.DataFrame({'Ay':m,'Satis':[0]*6})
        self.assertEqual(classify_group(df,'Z').sinif,'Talep yok')
        df.Satis=[0,0,2,0,0,0]
        self.assertEqual(classify_group(df,'Z').sinif,'Yetersiz pozitif veri')

    def test_wide_format(self):
        df,info=csv_read('Malzeme Kodu,2024-01,2024-02,2024-03\nA,2,,5\nB,0,0,1\n')
        self.assertEqual(info['format'],'geniş');self.assertEqual(len(df),6)
        self.assertEqual(df[(df.Malzeme=='A')].Satis.tolist(),[2,0,5])

    def test_threshold_cv2_population(self):
        m=pd.date_range('2024-01-01',periods=4,freq='MS')
        g=pd.DataFrame({'Ay':m,'Satis':[1,1,1,5]})
        s=classify_group(g,'A')
        self.assertAlmostEqual(s.cv2,.75)
        self.assertEqual(s.sinif,'Erratic')

    def test_real_sample(self):
        path=Path(__file__).resolve().parents[1]/'data'/'ornek_satis.csv'
        if path.exists():
            with path.open('rb') as f:
                df,_=read_sales_file(f,path.name)
            kinds=set(classify_all(df)['Talep sınıfı'])
            self.assertTrue({'Smooth','Erratic','Intermittent','Lumpy'}.issubset(kinds))


if __name__=='__main__': unittest.main()
