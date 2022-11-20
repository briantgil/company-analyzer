from statistics import mean


class CompanyAnalyzer():

    def __init__(self, mcap=0, oshares=0, beta=0.0, ptimcome=0, tax=0, tdebt=0, intex=0, fcf=[], afcfgr=0, is_afcfgr_given=False):
        self._risk_free_rate: float = 0.04181  #ust 5yr; source: cnbc; match bond term with investment duration
        self._market_rate: float  = 0.0796  #s&p 500; source: investopedia
        self._terminal_growth_rate: float = 0.0293  #gdp; source: world bank        
        self._margin_of_safety: float  = 0.30
        self._in_xds_of_dollars: int = 1000
        self._investment_duration_years = 5

        self._stock_price: float = 0.0
        self._dividend_per_share: float = 0.0
        self._dividend_growth_rate: float = 0.0

        self._market_cap: int = mcap  #reduced to match in same terms as debt
        self._outstanding_shares: int = oshares
        self._beta: float = beta
        self._pretax_income: int = ptimcome
        self._income_tax: int = tax  #if tax<0, tax rate=0%
        self._total_debt: int = tdebt  #use total debt and total assets for debt ratio; use total debt for WACC
        self._interest_ex: int = intex  #if interest income – interest expense > 0, then nii
        #newest -> oldest values
        self._free_cash_flows: list[int] = fcf  #fcf=operating cash flow-capex (purchases of premises, equipment, and leased equipment)

        self._avg_fcf_growth_rate: float = afcfgr          #accept a different avg fcf growth rate
        self._is_afcfgr_given: bool = is_afcfgr_given        

        self._is_data_loaded = False   #TODO: prevent operations if data is not loaded
        
        #TODO: generate file in controller, or separate module by using web scraping or rest api


    def __str__(self) -> str:
        #TODO: show 1yr, 2yr, 3yr cumulative growth and average change
        #TODO: show compare present value with market price
        #TODO: use color        
        #FIXME: rounding issue; from decimal import *
        pass


    def LoadCompanyFromTextFile(self, fd: str) -> bool:
        """load data from text file in a specific format"""
        pass
        

    def PrintToConsole(self) -> None:
        """print company analysis to console"""
        print(self)


    def Fair_Value(self) -> tuple[float]:
        """calculate fair value of stock price after margin of safety"""
        fair_value = sum(self.Discounted_FCF()) / self._outstanding_shares * self._in_xds_of_dollars
        value_after_magin_of_safety = fair_value * self._margin_of_safety
        return round(fair_value, 2), round(value_after_magin_of_safety, 2)


    def Discounted_FCF(self) -> list[float]:
        """calculate discounted free cash flows"""
        dfcf = []
        ffcf = self.Future_FCF()
        tv = self.PGM_Terminal_Value()  #XXX: method also gets future fcf
        df = self.Discount_Factors()
        for i in range(len(ffcf)):
            dfcf.append(ffcf[i] * df[i])
        dfcf.append(tv * df[-1])
        return dfcf


    def Discount_Factors(self) -> list[float]:
        """calculate discount factors for net present value (NPV)"""
        df = []
        dr = self.WACC_Discount_Rate()
        for i in range(self._investment_duration_years): 
            df.append(1/((1+dr)**(i+1)))
        return df


    def Future_FCF(self) -> list[float]:
        """calculate future free cash flows"""
        ffcf = []
        gr = None
        avg_gr = 0

        if self._is_afcfgr_given:
            avg_gr = self._avg_fcf_growth_rate
        else:
            gr = self.Growth_Rates(self._free_cash_flows)
            avg_gr = self.Average_Growth_Rate(gr)

        fcf_prev = self._free_cash_flows[0] * self._in_xds_of_dollars
        fcf_next = 0
        for i in range(self._investment_duration_years):
            fcf_next = fcf_prev * (1+avg_gr) * (i+1)
            ffcf.append(fcf_next)
            fcf_prev = fcf_next
        return ffcf


    def PGM_Terminal_Value(self) -> float:
        """calculate company's terminal value using perpetual growth model (PGM)"""
        fcf = self.Future_FCF()[-1]  #last forecast year; newest -> oldest values
        g = self._terminal_growth_rate
        d = self.WACC_Discount_Rate()
        #return round(fcf * (1+g) / (d-g), 2)
        return fcf * (1+g) / (d-g)


    def WACC_Discount_Rate(self) -> float:
        """calculate required rate of return (RRR) using Weighted Average Cost of Capital (WACC)"""
        v = self._market_cap + self._total_debt
        re = self.CAPM_Cost_Of_Equity()
        rd = self.Cost_Of_Debt()
        tc = self.Tax_Rate()
        #return round( (self._market_cap / v * re) + (self._total_debt / v * rd * (1-tc)) , 4)
        return (self._market_cap / v * re) + (self._total_debt / v * rd * (1-tc))


    def CAPM_Cost_Of_Equity(self) -> float:
        """calculate cost of equity using capital asset pricing model (CAPM)"""
        #mr-rfr=equity risk premium
        #return round(self._risk_free_rate + self._beta * (self._market_rate - self._risk_free_rate), 4)
        return self._risk_free_rate + self._beta * (self._market_rate - self._risk_free_rate) 


    def DCM_Cost_Of_Equity(self) -> float:
        """calculate cost of equity using dividend captialization model (DCM)"""
        #cost of equity does include dividend; it is return company must produce to shareholders
        raise NotImplementedError("DCM is not implemented, must use CAPM")
        return round(self._dividend_per_share/self._stock_price + self._dividend_growth_rate, 4)


    def Cost_Of_Debt(self) -> float:
            """calculate effective interest rate"""
            return self._Normalize_Rate(self._interest_ex, self._total_debt)


    def Tax_Rate(self) -> float:
            """calculate effective corporate tax rate"""
            return self._Normalize_Rate(self._income_tax, self._pretax_income)


    def _Normalize_Rate(self, n: int, d: int) -> float:    
        """calculate normalized interest or tax rate"""
        if not type(n) is int: raise TypeError("arg 1 must be integer")
        if not type(d) is int: raise TypeError("arg 2 must be integer")

        if n <= 0 or d <= 0: return 0.0
        #return round(n / d, 4)
        return n / d 


    def Growth_Rates(self, nums: list[int]) -> list[float]:
        """calculate QoQ or YoY growth rates"""
        if not type(nums) is list: raise TypeError("arg 1 must be list")
        if len(nums) < 2: raise ValueError("compare list must have at least 2 numbers to compare")
        if 0 in nums: raise ValueError("compare list must not have any 0s")

        #runs n-1 times
        gr: list[float] = []
        for i in range(len(nums)-1, 0, -1):
            gr.append(self._Period_Over_Period_Growth_Rate(nums[i-1], nums[i]))
        return gr


    def _Period_Over_Period_Growth_Rate(self, n: int, m: int) -> float:
        """calculate MoM, QoQ, or YoY growth rate"""
        if not type(m) is int: raise TypeError("arg 1 must be integer")
        if not type(n) is int: raise TypeError("arg 2 must be integer")
        if m == 0: raise ZeroDivisionError("division by zero")

        #XXX: if comparing -/+ or +/-, PoP=0
        #if m < 0: return round((n - m) / abs(m), 4)
        if m < 0 or n < 0: return round(0, 4)
        #return round((n - m) / m, 4)
        return (n - m) / m


    def Average_Growth_Rate(self, rates: list[float]) -> float:
        """calculate average PoP growth rate"""
        if not type(rates) is list: raise TypeError("arg 1 must be list")
        if len(rates) == 0: raise ValueError("list must have at least one value")

        #return round(mean(rates), 4)
        return mean(rates)


    def Cumulative_Growth_Rates(self) -> list[float]:
        """calculate cumulative growth rates for last 1yr, 2yr, etc"""
        pass



if __name__ == '__main__':
    market_cap = 721609664
    outstanding_shares = 3157753
    beta = 2.11
    pretax_income = 6343000
    income_tax = 699000
    total_debt = 33723000	
    interest_ex = 371000
    free_cash_flows = [3515000, 2786000, 1078000, -3000, -3476000]

    tsla = CompanyAnalyzer(market_cap, outstanding_shares, beta, pretax_income, income_tax, total_debt, interest_ex, free_cash_flows)
    print(f"fcf={tsla._free_cash_flows}")
    gr = tsla.Growth_Rates(tsla._free_cash_flows)
    print(f"gr={gr}")
    avg_gr = tsla.Average_Growth_Rate(gr)
    print(f"avg gr={avg_gr}")
    print(f"coe={tsla.CAPM_Cost_Of_Equity()}")
    print(f"cod={tsla.Cost_Of_Debt()}")
    print(f"tax rate={tsla.Tax_Rate()}")
    wacc = tsla.WACC_Discount_Rate()
    print(f"wacc={wacc}")
    tv = tsla.PGM_Terminal_Value()
    print(f"tv={tv}")
    ffcf = tsla.Future_FCF()
    print(f"ffcf={ffcf}\n")
    df = tsla.Discount_Factors()
    print(f"df={df}\n")
    dcf = tsla.Discounted_FCF()
    print(f"dcf={dcf}\n")
    fv, mos = tsla.Fair_Value()
    print(f"fv={fv}")
    print(f"mos={mos}")

    #TODO: unit tests


"""
market_cap:721,609,664
outstanding_shares:3,157,753
beta:2.11
pretax_income:6,343,000
income_tax:699,000
total_debt:33,723,000	
interest_ex:371,000
free_cash_flows:3,515,000	2,786,000	1,078,000	-3,000	-3,476,000
avg_fcf_growth_rate:
"""
