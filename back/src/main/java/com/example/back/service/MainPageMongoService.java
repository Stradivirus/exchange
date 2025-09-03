package com.example.back.service;

import com.example.back.dto.MainPageResponseDto;
import com.example.back.mongo.*;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;

@Service
@RequiredArgsConstructor
public class MainPageMongoService {
    private final GoldRepository goldRepository;
    private final SilverRepository silverRepository;
    private final CrudeOilRepository crudeOilRepository;
    private final BrentOilRepository brentOilRepository;
    private final CopperRepository copperRepository;
    private final DxyRepository dxyRepository;
    private final VixRepository vixRepository;
    private final UsdRepository usdRepository;
    private final JpyRepository jpyRepository;
    private final EurRepository eurRepository;
    private final CnyRepository cnyRepository;
    private final Sp500Repository sp500Repository;
    private final DowJonesRepository dowJonesRepository;
    private final NasdaqRepository nasdaqRepository;
    private final KospiRepository kospiRepository;
    private final KosdaqRepository kosdaqRepository;
    private final KorBaseRateRepository korBaseRateRepository;
    private final UsFedRateRepository usFedRateRepository;

    public MainPageResponseDto getLatestMainPageInfo() {
        Gold gold = goldRepository.findTopByOrderByDateDesc();
        Silver silver = silverRepository.findTopByOrderByDateDesc();
        CrudeOil crudeOil = crudeOilRepository.findTopByOrderByDateDesc();
        BrentOil brentOil = brentOilRepository.findTopByOrderByDateDesc();
        Copper copper = copperRepository.findTopByOrderByDateDesc();
        Dxy dxy = dxyRepository.findTopByOrderByDateDesc();
        Vix vix = vixRepository.findTopByOrderByDateDesc();
        Usd usd = usdRepository.findTopByOrderByDateDesc();
        Jpy jpy = jpyRepository.findTopByOrderByDateDesc();
        Eur eur = eurRepository.findTopByOrderByDateDesc();
        Cny cny = cnyRepository.findTopByOrderByDateDesc();
        Sp500 sp500 = sp500Repository.findTopByOrderByDateDesc();
        DowJones dowJones = dowJonesRepository.findTopByOrderByDateDesc();
        Nasdaq nasdaq = nasdaqRepository.findTopByOrderByDateDesc();
        Kospi kospi = kospiRepository.findTopByOrderByDateDesc();
        Kosdaq kosdaq = kosdaqRepository.findTopByOrderByDateDesc();
        KorBaseRate korBaseRate = korBaseRateRepository.findTopByOrderByDateDesc();
        UsFedRate usFedRate = usFedRateRepository.findTopByOrderByDateDesc();

        com.example.back.dto.CommoditiesDto commodities = com.example.back.dto.CommoditiesDto.builder()
            .date(gold != null ? gold.getDate().toString() : null)
            .gold(gold != null ? gold.getClose() : null)
            .silver(silver != null ? silver.getClose() : null)
            .copper(copper != null ? copper.getClose() : null)
            .crudeOil(crudeOil != null ? crudeOil.getClose() : null)
            .brentOil(brentOil != null ? brentOil.getClose() : null)
            .build();

        com.example.back.dto.CommoditiesIndexDto commoditiesIndex = com.example.back.dto.CommoditiesIndexDto.builder()
            .date(dxy != null ? dxy.getDate().toString() : null)
            .dxy(dxy != null ? dxy.getClose() : null)
            .vix(vix != null ? vix.getClose() : null)
            .build();

        com.example.back.dto.ExchangeDto exchange = com.example.back.dto.ExchangeDto.builder()
            .date(usd != null ? usd.getDate().toString() : null)
            .usd(usd != null ? usd.getRate() : null)
            .jpy(jpy != null ? jpy.getRate() : null)
            .eur(eur != null ? eur.getRate() : null)
            .cny(cny != null ? cny.getRate() : null)
            .build();

        com.example.back.dto.InterestRateDto interestRate = com.example.back.dto.InterestRateDto.builder()
            .date(korBaseRate != null ? korBaseRate.getDate().toString() : null)
            .korBaseRate(korBaseRate != null ? korBaseRate.getRate() : null)
            .usFedRate(usFedRate != null ? usFedRate.getRate() : null)
            .build();

        com.example.back.dto.StockDto stock = com.example.back.dto.StockDto.builder()
            .date(sp500 != null ? sp500.getDate().toString() : null)
            .sp500(sp500 != null ? sp500.getClose() : null)
            .dowJones(dowJones != null ? dowJones.getClose() : null)
            .nasdaq(nasdaq != null ? nasdaq.getClose() : null)
            .kospi(kospi != null ? kospi.getClose() : null)
            .kosdaq(kosdaq != null ? kosdaq.getClose() : null)
            .build();

        return com.example.back.dto.MainPageResponseDto.builder()
            .commodities(commodities)
            .commoditiesIndex(commoditiesIndex)
            .exchange(exchange)
            .interestRate(interestRate)
            .stock(stock)
            .build();
    }
}
