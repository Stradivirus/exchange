package com.example.back.service;

import com.example.back.dto.MainPageResponseDto;
import com.example.back.dto.grains.*;
import com.example.back.dto.commodities.*;
import com.example.back.dto.commodities_index.*;
import com.example.back.dto.exchange.*;
import com.example.back.dto.interest.*;
import com.example.back.dto.stock.*;
import com.example.back.mongo.commodities.*;
import com.example.back.mongo.commodities_index.*;
import com.example.back.mongo.exchange.*;
import com.example.back.mongo.interest.*;
import com.example.back.mongo.stock.*;
import com.example.back.mongo.grains.*;
import java.util.Collections;
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
    private final RiceRepository riceRepository;
    private final WheatRepository wheatRepository;
    private final CornRepository cornRepository;
    private final CoffeeRepository coffeeRepository;
    private final SugarRepository sugarRepository;

    public MainPageResponseDto getLatestMainPageInfo() {
    // grains
    Rice rice = riceRepository.findTopByOrderByDateDesc();
    Wheat wheat = wheatRepository.findTopByOrderByDateDesc();
    Corn corn = cornRepository.findTopByOrderByDateDesc();
    Coffee coffee = coffeeRepository.findTopByOrderByDateDesc();
    Sugar sugar = sugarRepository.findTopByOrderByDateDesc();

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

        return MainPageResponseDto.builder()
            // grains
            .riceList(rice != null ? Collections.singletonList(RiceDto.builder()
                .date(rice.getDate())
                .close(rice.getClose())
                .open(rice.getOpen())
                .high(rice.getHigh())
                .low(rice.getLow())
                .volume(rice.getVolume())
                .price(rice.getPrice())
                .created_at(rice.getCreated_at())
                .build()) : Collections.emptyList())
            .wheatList(wheat != null ? Collections.singletonList(WheatDto.builder()
                .date(wheat.getDate())
                .close(wheat.getClose())
                .open(wheat.getOpen())
                .high(wheat.getHigh())
                .low(wheat.getLow())
                .volume(wheat.getVolume())
                .price(wheat.getPrice())
                .created_at(wheat.getCreated_at())
                .build()) : Collections.emptyList())
            .cornList(corn != null ? Collections.singletonList(CornDto.builder()
                .date(corn.getDate())
                .close(corn.getClose())
                .open(corn.getOpen())
                .high(corn.getHigh())
                .low(corn.getLow())
                .volume(corn.getVolume())
                .price(corn.getPrice())
                .created_at(corn.getCreated_at())
                .build()) : Collections.emptyList())
            .coffeeList(coffee != null ? Collections.singletonList(CoffeeDto.builder()
                .date(coffee.getDate())
                .close(coffee.getClose())
                .open(coffee.getOpen())
                .high(coffee.getHigh())
                .low(coffee.getLow())
                .volume(coffee.getVolume())
                .price(coffee.getPrice())
                .created_at(coffee.getCreated_at())
                .build()) : Collections.emptyList())
            .sugarList(sugar != null ? Collections.singletonList(SugarDto.builder()
                .date(sugar.getDate())
                .close(sugar.getClose())
                .open(sugar.getOpen())
                .high(sugar.getHigh())
                .low(sugar.getLow())
                .volume(sugar.getVolume())
                .price(sugar.getPrice())
                .created_at(sugar.getCreated_at())
                .build()) : Collections.emptyList())

            // commodities
            .goldList(gold != null ? Collections.singletonList(GoldDto.builder()
                .date(gold.getDate())
                .close(gold.getClose())
                .open(gold.getOpen())
                .high(gold.getHigh())
                .low(gold.getLow())
                .volume(gold.getVolume())
                .price(gold.getPrice())
                .created_at(gold.getCreated_at())
                .build()) : Collections.emptyList())
            .silverList(silver != null ? Collections.singletonList(SilverDto.builder()
                .date(silver.getDate())
                .close(silver.getClose())
                .open(silver.getOpen())
                .high(silver.getHigh())
                .low(silver.getLow())
                .volume(silver.getVolume())
                .price(silver.getPrice())
                .created_at(silver.getCreated_at())
                .build()) : Collections.emptyList())
            .copperList(copper != null ? Collections.singletonList(CopperDto.builder()
                .date(copper.getDate())
                .close(copper.getClose())
                .open(copper.getOpen())
                .high(copper.getHigh())
                .low(copper.getLow())
                .volume(copper.getVolume())
                .price(copper.getPrice())
                .created_at(copper.getCreated_at())
                .build()) : Collections.emptyList())
            .crudeOilList(crudeOil != null ? Collections.singletonList(CrudeOilDto.builder()
                .date(crudeOil.getDate())
                .close(crudeOil.getClose())
                .open(crudeOil.getOpen())
                .high(crudeOil.getHigh())
                .low(crudeOil.getLow())
                .volume(crudeOil.getVolume())
                .price(crudeOil.getPrice())
                .created_at(crudeOil.getCreated_at())
                .build()) : Collections.emptyList())
            .brentOilList(brentOil != null ? Collections.singletonList(BrentOilDto.builder()
                .date(brentOil.getDate())
                .close(brentOil.getClose())
                .open(brentOil.getOpen())
                .high(brentOil.getHigh())
                .low(brentOil.getLow())
                .volume(brentOil.getVolume())
                .price(brentOil.getPrice())
                .created_at(brentOil.getCreated_at())
                .build()) : Collections.emptyList())

            // commodities index
            .dxyList(dxy != null ? Collections.singletonList(DxyDto.builder()
                .date(dxy.getDate())
                .close(dxy.getClose())
                .open(dxy.getOpen())
                .high(dxy.getHigh())
                .low(dxy.getLow())
                .volume(dxy.getVolume())
                .price(dxy.getPrice())
                .created_at(dxy.getCreated_at())
                .build()) : Collections.emptyList())
            .vixList(vix != null ? Collections.singletonList(VixDto.builder()
                .date(vix.getDate())
                .close(vix.getClose())
                .open(vix.getOpen())
                .high(vix.getHigh())
                .low(vix.getLow())
                .volume(vix.getVolume())
                .price(vix.getPrice())
                .created_at(vix.getCreated_at())
                .build()) : Collections.emptyList())

            // exchange
            .usdList(usd != null ? Collections.singletonList(UsdDto.builder()
                .date(usd.getDate())
                .rate(usd.getRate())
                .currency_code(usd.getCurrency_code())
                .unit_name(usd.getUnit_name())
                .created_at(usd.getCreated_at())
                .build()) : Collections.emptyList())
            .jpyList(jpy != null ? Collections.singletonList(JpyDto.builder()
                .date(jpy.getDate())
                .rate(jpy.getRate())
                .currency_code(jpy.getCurrency_code())
                .unit_name(jpy.getUnit_name())
                .created_at(jpy.getCreated_at())
                .build()) : Collections.emptyList())
            .eurList(eur != null ? Collections.singletonList(EurDto.builder()
                .date(eur.getDate())
                .rate(eur.getRate())
                .currency_code(eur.getCurrency_code())
                .unit_name(eur.getUnit_name())
                .created_at(eur.getCreated_at())
                .build()) : Collections.emptyList())
            .cnyList(cny != null ? Collections.singletonList(CnyDto.builder()
                .date(cny.getDate())
                .rate(cny.getRate())
                .currency_code(cny.getCurrency_code())
                .unit_name(cny.getUnit_name())
                .created_at(cny.getCreated_at())
                .build()) : Collections.emptyList())

            // interest
            .korBaseRateList(korBaseRate != null ? Collections.singletonList(KorBaseRateDto.builder()
                .date(korBaseRate.getDate())
                .rate(korBaseRate.getRate())
                .created_at(korBaseRate.getCreated_at())
                .build()) : Collections.emptyList())
            .usFedRateList(usFedRate != null ? Collections.singletonList(UsFedRateDto.builder()
                .date(usFedRate.getDate())
                .rate(usFedRate.getRate())
                .created_at(usFedRate.getCreated_at())
                .build()) : Collections.emptyList())

            // stock
            .sp500List(sp500 != null ? Collections.singletonList(Sp500Dto.builder()
                .date(sp500.getDate())
                .close(sp500.getClose())
                .open(sp500.getOpen())
                .high(sp500.getHigh())
                .low(sp500.getLow())
                .volume(sp500.getVolume())
                .price(sp500.getPrice())
                .created_at(sp500.getCreated_at())
                .build()) : Collections.emptyList())
            .dowJonesList(dowJones != null ? Collections.singletonList(DowJonesDto.builder()
                .date(dowJones.getDate())
                .close(dowJones.getClose())
                .open(dowJones.getOpen())
                .high(dowJones.getHigh())
                .low(dowJones.getLow())
                .volume(dowJones.getVolume())
                .price(dowJones.getPrice())
                .created_at(dowJones.getCreated_at())
                .build()) : Collections.emptyList())
            .nasdaqList(nasdaq != null ? Collections.singletonList(NasdaqDto.builder()
                .date(nasdaq.getDate())
                .close(nasdaq.getClose())
                .open(nasdaq.getOpen())
                .high(nasdaq.getHigh())
                .low(nasdaq.getLow())
                .volume(nasdaq.getVolume())
                .price(nasdaq.getPrice())
                .created_at(nasdaq.getCreated_at())
                .build()) : Collections.emptyList())
            .kospiList(kospi != null ? Collections.singletonList(KospiDto.builder()
                .date(kospi.getDate())
                .close(kospi.getClose())
                .open(kospi.getOpen())
                .high(kospi.getHigh())
                .low(kospi.getLow())
                .volume(kospi.getVolume())
                .price(kospi.getPrice())
                .created_at(kospi.getCreated_at())
                .build()) : Collections.emptyList())
            .kosdaqList(kosdaq != null ? Collections.singletonList(KosdaqDto.builder()
                .date(kosdaq.getDate())
                .close(kosdaq.getClose())
                .open(kosdaq.getOpen())
                .high(kosdaq.getHigh())
                .low(kosdaq.getLow())
                .volume(kosdaq.getVolume())
                .price(kosdaq.getPrice())
                .created_at(kosdaq.getCreated_at())
                .build()) : Collections.emptyList())
            .build();
    }
}
