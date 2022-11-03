from statistics import mean


class CompanyAnalyzer():

    def __init__(self, market_cap=0, outstanding_shares=0, beta=0.0, pretax_imcome=0, income_tax=0, total_debt=0, interest_ex=0):

        self._stock_price: float = 0.0
        self._dividend_per_share: float = 0.0
        self._dividend_growth_rate: float = 0.0

        self._market_cap: int = market_cap  #reduced to match in same terms as debt
        self._outstanding_shares: int = outstanding_shares
        self._beta: float = beta
        
        self._pretax_income: int = pretax_imcome
        self._income_tax: int = income_tax  #if tax<0, tax rate=0%
        
        self._total_debt: int = total_debt  #use total debt and total assets for debt ratio; use total debt for WACC
        self._interest_ex: int = interest_ex  #if interest income – interest expense > 0, then nii

        self._risk_free_rate: float = 0.04181  #ust 5yr; source: cnbc; match bond term with investment duration
        self._market_rate: float  = 0.0796  #s&p 500; source: investopedia
        self._terminal_growth_rate: float = 0.0293  #gdp; source: world bank        
        self._margin_of_safety: float  = 0.30
        self._in_xds_of_dollars: int = 1000
        self._investment_duration_years = 5

        #newest -> oldest values
        self._free_cash_flows: list[int] = []  #fcf=operating cash flow-capex (purchases of premises, equipment, and leased equipment)

        #oldest -> newest values
        self._future_fcf: list[float] = []  
        self._discount_factors: list[float] = []  
        self._discounted_fcf: list[float] = []  

        self._other_metric: list[int] = [] 


    def __str__(self) -> str:
        pass


    def LoadCompanyFromFile(self, fd: str) -> bool:
        pass


    def PrintCompanyMetrics(self) -> str:
        #TODO: show 1yr, 2yr, 3yr cumulative growth and average change
        #TODO: show compare present value with market price
        #TODO: accept a different avg fcf growth rate
        pass


    def _TaxRate(self) -> float:
            """calculate effective corporate tax rate"""
            return self._NormalizedRate(self._income_tax, self._pretax_income)


    def _CostOfDebt(self) -> float:
            """calculate effective interest rate"""
            return self._NormalizedRate(self._interest_ex, self._total_debt)


    def _CostOfEquity_DCM(self) -> float:
        """calculate cost of equity using dividend captialization model (DCM)"""
        #cost of equity does include dividend; it is return company must produce to shareholders
        raise NotImplementedError("DCM is not implemented, must use CAPM")
        return round(self._dividend_per_share/self._stock_price + self._dividend_growth_rate, 4)


    def _CostOfEquity_CAPM(self) -> float:
        """calculate cost of equity using capital asset pricing model (CAPM)"""
        #mr-rfr=equity risk premium
        return round(self._risk_free_rate + self._beta * (self._market_rate - self._risk_free_rate), 4)  


    def _DiscountRate_WACC(self) -> float:
        """calculate required rate of return (RRR) using Weighted Average Cost of Capital (WACC)"""
        v = self._market_cap + self._total_debt
        re = self._CostOfEquity_CAPM()
        rd = self._CostOfDebt()
        tc = self._TaxRate()
        return round( (self._market_cap / v * re) + (self._total_debt / v * rd * (1-tc)) , 4)


    def _TerminalValue_PGM(self) -> float:
        """calculate company's terminal value using perpetual growth model (PGM)"""
        fcf = self._free_cash_flows[0]  #last forecast year; newest -> oldest values
        g = self._terminal_growth_rate
        d = self._DiscountRate_WACC()
        return round(fcf * (1+g) / (d-g), 2)


    def _DiscountFactors(self) -> None:
        """calculate discount factors for net present value (NPV)"""
        d = self._DiscountRate_WACC()
        for i in range(self._investment_duration_years): 
            self._discount_factors.append(1/((1+d)**(i+1)))
        self._discount_factors.append(1/((1+d)**(self._investment_duration_years)))


    def _FutureFCF(self) -> None:
        """calculate future free cash flows"""
        tv = self._TerminalValue_PGM()
        gr = self.GrowthRates(self._free_cash_flows)
        avg_gr = self.AverageGrowthRate(gr)

        fcf_prev = self._free_cash_flows[0] * self._in_xds_of_dollars
        fcf_next = 0
        for i in range(self._investment_duration_years):
            fcf_next = fcf_prev * (1+avg_gr)
            self._future_fcf.append(fcf_next)
            fcf_prev = fcf_next
        self._future_fcf.append(tv)


    def _DiscountedFCF(self) -> None:
        """calculate discounted free cash flows"""
        for i in range(len(self._furture_fcf)):
            self._discounted_fcf.append(self._furture_fcf[i] * self._discount_factors[i])

    
    def _FairValue(self) -> tuple[float]:
        """calculate fair value of stock price after margin of safety"""
        total_discounted_fcf = sum(self._discounted_fcf)
        fair_value = total_discounted_fcf / self._outstanding_shares * self._in_xds_of_dollars
        value_after_magin_of_safety = fair_value * self._margin_of_safety
        return fair_value, value_after_magin_of_safety


    def _NormalizedRate(self, n: int, d: int) -> float:    
        """calculate normalized interest or tax rate"""
        if not type(n) is int: raise TypeError("arg 1 must be integer")
        if not type(d) is int: raise TypeError("arg 2 must be integer")

        if n <= 0 or d <= 0: return 0.0
        return round(n / d, 4) 


    def GrowthRates(self, nums: list[int]) -> list[float]:
        """calculate QoQ or YoY growth rates"""
        if not type(nums) is list: raise TypeError("arg 1 must be list")
        if len(nums) < 2: raise ValueError("compare list must have at least 2 numbers to compare")
        if 0 in nums: raise ValueError("compare list must not have any 0s")

        #runs n-1 times
        gr: list[float] = []
        for i in range(len(nums)-1, 0, -1):
            gr.append(self._PeriodOverPeriodGrowthRate(nums[i-1], nums[i]))
        return gr


    def _PeriodOverPeriodGrowthRate(self, n: int, m: int) -> float:
        """calculate QoQ or YoY growth rate"""
        if not type(m) is int: raise TypeError("arg 1 must be integer")
        if not type(n) is int: raise TypeError("arg 2 must be integer")
        if m == 0: raise ZeroDivisionError("division by zero")

        if m < 0: return round((n - m) / abs(m), 4)
        return round((n - m) / m, 4)


    def AverageGrowthRate(self, nums: list[float]) -> float:
        """calculate average QoQ or YoY growth rate"""
        if not type(nums) is list: raise TypeError("arg 1 must be list")
        if len(nums) == 0: raise ValueError("list must have at least one value")

        return round(mean(nums), 4)



if __name__ == '__main__':
    pass

    #TODO: unit tests


