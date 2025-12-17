package com.example.back.service;

import com.example.back.dto.MainPageResponseDto;
import com.example.back.dto.grains.*;
import com.example.back.dto.commodities.*;
import com.example.back.dto.commodities_index.*;
import com.example.back.dto.exchange.*;
import com.example.back.dto.interest.*;
import com.example.back.dto.stock.*;
import com.example.back.dto.mental.*;

import com.example.back.mongo.commodities.*;
import com.example.back.mongo.commodities_index.*;
import com.example.back.mongo.exchange.*;
import com.example.back.mongo.interest.*;
import com.example.back.mongo.stock.*;
import com.example.back.mongo.grains.*;
import com.example.back.mongo.mental.*;

import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;

import java.time.LocalDate;
import java.time.ZoneId;
import java.util.*;
import java.util.stream.Collectors;

@Service
@RequiredArgsConstructor
public class MainPageMongoService {

    // --- Repository 주입 ---
    // Commodities
    private final GoldRepository goldRepository;
    private final SilverRepository silverRepository;
    private final CrudeOilRepository crudeOilRepository;
    private final BrentOilRepository brentOilRepository;
    private final CopperRepository copperRepository;

    // Index
    private final DxyRepository dxyRepository;
    private final VixRepository vixRepository;

    // Exchange
    private final UsdRepository usdRepository;
    private final JpyRepository jpyRepository;
    private final EurRepository eurRepository;
    private final CnyRepository cnyRepository;

    // Stock
    private final Sp500Repository sp500Repository;
    private final DowJonesRepository dowJonesRepository;
    private final NasdaqRepository nasdaqRepository;
    private final KospiRepository kospiRepository;
    private final KosdaqRepository kosdaqRepository;

    // Interest
    private final KorBaseRateRepository korBaseRateRepository;
    private final UsFedRateRepository usFedRateRepository;

    // Grains
    private final RiceRepository riceRepository;
    private final WheatRepository wheatRepository;
    private final CornRepository cornRepository;
    private final CoffeeRepository coffeeRepository;
    private final SugarRepository sugarRepository;

    // Mental
    private final ConsumerSentimentRepository consumerSentimentRepository;
    private final EconomicSentimentRepository economicSentimentRepository;
    private final NewsSentimentRepository newsSentimentRepository;

    // =================================================================================
    // 기존 기능: 메인 페이지용 최신 데이터 1건씩 조회
    // =================================================================================
    public MainPageResponseDto getLatestMainPageInfo() {
        // grains
        Rice rice = riceRepository.findTopByOrderByDateDesc();
        Wheat wheat = wheatRepository.findTopByOrderByDateDesc();
        Corn corn = cornRepository.findTopByOrderByDateDesc();
        Coffee coffee = coffeeRepository.findTopByOrderByDateDesc();
        Sugar sugar = sugarRepository.findTopByOrderByDateDesc();

        // commodities
        Gold gold = goldRepository.findTopByOrderByDateDesc();
        Silver silver = silverRepository.findTopByOrderByDateDesc();
        CrudeOil crudeOil = crudeOilRepository.findTopByOrderByDateDesc();
        BrentOil brentOil = brentOilRepository.findTopByOrderByDateDesc();
        Copper copper = copperRepository.findTopByOrderByDateDesc();

        // index
        Dxy dxy = dxyRepository.findTopByOrderByDateDesc();
        Vix vix = vixRepository.findTopByOrderByDateDesc();

        // exchange
        Usd usd = usdRepository.findTopByOrderByDateDesc();
        Jpy jpy = jpyRepository.findTopByOrderByDateDesc();
        Eur eur = eurRepository.findTopByOrderByDateDesc();
        Cny cny = cnyRepository.findTopByOrderByDateDesc();

        // stock
        Sp500 sp500 = sp500Repository.findTopByOrderByDateDesc();
        DowJones dowJones = dowJonesRepository.findTopByOrderByDateDesc();
        Nasdaq nasdaq = nasdaqRepository.findTopByOrderByDateDesc();
        Kospi kospi = kospiRepository.findTopByOrderByDateDesc();
        Kosdaq kosdaq = kosdaqRepository.findTopByOrderByDateDesc();

        // interest
        KorBaseRate korBaseRate = korBaseRateRepository.findTopByOrderByDateDesc();
        UsFedRate usFedRate = usFedRateRepository.findTopByOrderByDateDesc();

        // mental
        ConsumerSentiment consumerSentiment = consumerSentimentRepository.findTopByOrderByDateDesc();
        EconomicSentiment economicSentiment = economicSentimentRepository.findTopByOrderByDateDesc();
        List<NewsSentiment> newsSentimentList = newsSentimentRepository.findTop5ByOrderByDateDesc();

        return MainPageResponseDto.builder()
                // grains
                .riceList(rice != null ? Collections.singletonList(RiceDto.builder().date(rice.getDate()).close(rice.getClose()).open(rice.getOpen()).high(rice.getHigh()).low(rice.getLow()).volume(rice.getVolume()).build()) : Collections.emptyList())
                .wheatList(wheat != null ? Collections.singletonList(WheatDto.builder().date(wheat.getDate()).close(wheat.getClose()).open(wheat.getOpen()).high(wheat.getHigh()).low(wheat.getLow()).volume(wheat.getVolume()).build()) : Collections.emptyList())
                .cornList(corn != null ? Collections.singletonList(CornDto.builder().date(corn.getDate()).close(corn.getClose()).open(corn.getOpen()).high(corn.getHigh()).low(corn.getLow()).volume(corn.getVolume()).build()) : Collections.emptyList())
                .coffeeList(coffee != null ? Collections.singletonList(CoffeeDto.builder().date(coffee.getDate()).close(coffee.getClose()).open(coffee.getOpen()).high(coffee.getHigh()).low(coffee.getLow()).volume(coffee.getVolume()).build()) : Collections.emptyList())
                .sugarList(sugar != null ? Collections.singletonList(SugarDto.builder().date(sugar.getDate()).close(sugar.getClose()).open(sugar.getOpen()).high(sugar.getHigh()).low(sugar.getLow()).volume(sugar.getVolume()).build()) : Collections.emptyList())

                // commodities
                .goldList(gold != null ? Collections.singletonList(GoldDto.builder().date(gold.getDate()).close(gold.getClose()).open(gold.getOpen()).high(gold.getHigh()).low(gold.getLow()).volume(gold.getVolume()).build()) : Collections.emptyList())
                .silverList(silver != null ? Collections.singletonList(SilverDto.builder().date(silver.getDate()).close(silver.getClose()).open(silver.getOpen()).high(silver.getHigh()).low(silver.getLow()).volume(silver.getVolume()).build()) : Collections.emptyList())
                .copperList(copper != null ? Collections.singletonList(CopperDto.builder().date(copper.getDate()).close(copper.getClose()).open(copper.getOpen()).high(copper.getHigh()).low(copper.getLow()).volume(copper.getVolume()).build()) : Collections.emptyList())
                .crudeOilList(crudeOil != null ? Collections.singletonList(CrudeOilDto.builder().date(crudeOil.getDate()).close(crudeOil.getClose()).open(crudeOil.getOpen()).high(crudeOil.getHigh()).low(crudeOil.getLow()).volume(crudeOil.getVolume()).build()) : Collections.emptyList())
                .brentOilList(brentOil != null ? Collections.singletonList(BrentOilDto.builder().date(brentOil.getDate()).close(brentOil.getClose()).open(brentOil.getOpen()).high(brentOil.getHigh()).low(brentOil.getLow()).volume(brentOil.getVolume()).build()) : Collections.emptyList())

                // commodities index
                .dxyList(dxy != null ? Collections.singletonList(DxyDto.builder().date(dxy.getDate()).close(dxy.getClose()).open(dxy.getOpen()).high(dxy.getHigh()).low(dxy.getLow()).build()) : Collections.emptyList())
                .vixList(vix != null ? Collections.singletonList(VixDto.builder().date(vix.getDate()).close(vix.getClose()).open(vix.getOpen()).high(vix.getHigh()).low(vix.getLow()).build()) : Collections.emptyList())

                // exchange
                .usdList(usd != null ? Collections.singletonList(UsdDto.builder().date(usd.getDate()).rate(usd.getRate()).unit_name(usd.getUnit_name()).build()) : Collections.emptyList())
                .jpyList(jpy != null ? Collections.singletonList(JpyDto.builder().date(jpy.getDate()).rate(jpy.getRate()).unit_name(jpy.getUnit_name()).build()) : Collections.emptyList())
                .eurList(eur != null ? Collections.singletonList(EurDto.builder().date(eur.getDate()).rate(eur.getRate()).unit_name(eur.getUnit_name()).build()) : Collections.emptyList())
                .cnyList(cny != null ? Collections.singletonList(CnyDto.builder().date(cny.getDate()).rate(cny.getRate()).unit_name(cny.getUnit_name()).build()) : Collections.emptyList())

                // interest
                .korBaseRateList(korBaseRate != null ? Collections.singletonList(KorBaseRateDto.builder().date(korBaseRate.getDate()).rate(korBaseRate.getRate()).build()) : Collections.emptyList())
                .usFedRateList(usFedRate != null ? Collections.singletonList(UsFedRateDto.builder().date(usFedRate.getDate()).rate(usFedRate.getRate()).build()) : Collections.emptyList())

                // stock
                .sp500List(sp500 != null ? Collections.singletonList(Sp500Dto.builder().date(sp500.getDate()).close(sp500.getClose()).open(sp500.getOpen()).high(sp500.getHigh()).low(sp500.getLow()).volume(sp500.getVolume()).build()) : Collections.emptyList())
                .dowJonesList(dowJones != null ? Collections.singletonList(DowJonesDto.builder().date(dowJones.getDate()).close(dowJones.getClose()).open(dowJones.getOpen()).high(dowJones.getHigh()).low(dowJones.getLow()).volume(dowJones.getVolume()).build()) : Collections.emptyList())
                .nasdaqList(nasdaq != null ? Collections.singletonList(NasdaqDto.builder().date(nasdaq.getDate()).close(nasdaq.getClose()).open(nasdaq.getOpen()).high(nasdaq.getHigh()).low(nasdaq.getLow()).volume(nasdaq.getVolume()).build()) : Collections.emptyList())
                .kospiList(kospi != null ? Collections.singletonList(KospiDto.builder().date(kospi.getDate()).close(kospi.getClose()).open(kospi.getOpen()).high(kospi.getHigh()).low(kospi.getLow()).volume(kospi.getVolume()).build()) : Collections.emptyList())
                .kosdaqList(kosdaq != null ? Collections.singletonList(KosdaqDto.builder().date(kosdaq.getDate()).close(kosdaq.getClose()).open(kosdaq.getOpen()).high(kosdaq.getHigh()).low(kosdaq.getLow()).volume(kosdaq.getVolume()).build()) : Collections.emptyList())

                // mental
                .consumerSentimentList(consumerSentiment != null ? Collections.singletonList(toConsumerSentimentDto(consumerSentiment)) : Collections.emptyList())
                .economicSentimentList(economicSentiment != null ? Collections.singletonList(toEconomicSentimentDto(economicSentiment)) : Collections.emptyList())
                .newsSentimentList(newsSentimentList != null && !newsSentimentList.isEmpty() ?
                        newsSentimentList.stream().map(this::toNewsSentimentDto).toList() : Collections.emptyList())
                .build();
    }


    // =================================================================================
    // [신규] 최근 30개 데이터 조회 및 병합 (Postgres 기능 대체)
    // =================================================================================

    // 1. 환율 30개 (ExchangeDto) -> ExchangeDto는 LocalDate 사용
    public List<ExchangeDto> getLatest30Exchange() {
        Map<LocalDate, ExchangeDto.ExchangeDtoBuilder> map = new HashMap<>();

        List<Usd> usdList = usdRepository.findTop30ByOrderByDateDesc();
        List<Jpy> jpyList = jpyRepository.findTop30ByOrderByDateDesc();
        List<Eur> eurList = eurRepository.findTop30ByOrderByDateDesc();
        List<Cny> cnyList = cnyRepository.findTop30ByOrderByDateDesc();

        usdList.forEach(e -> getBuilder(map, toLocalDate(e.getDate())).usd(e.getRate()));
        jpyList.forEach(e -> getBuilder(map, toLocalDate(e.getDate())).jpy(e.getRate()));
        eurList.forEach(e -> getBuilder(map, toLocalDate(e.getDate())).eur(e.getRate()));
        cnyList.forEach(e -> getBuilder(map, toLocalDate(e.getDate())).cny(e.getRate()));

        // ExchangeDto는 LocalDate를 사용하므로 그대로 build()
        return map.entrySet().stream()
                .sorted(Map.Entry.<LocalDate, ExchangeDto.ExchangeDtoBuilder>comparingByKey().reversed())
                .map(e -> e.getValue().build())
                .collect(Collectors.toList());
    }

    // 2. 곡물 30개 (GrainsDto) -> GrainsDto는 java.sql.Date 사용
    public List<GrainsDto> getLatest30GrainsDto() {
        Map<LocalDate, GrainsDto.GrainsDtoBuilder> map = new HashMap<>();

        riceRepository.findTop30ByOrderByDateDesc().forEach(e ->
                getGrainsBuilder(map, toLocalDate(e.getDate())).rice(e.getClose()).riceVolume(e.getVolume()));
        wheatRepository.findTop30ByOrderByDateDesc().forEach(e ->
                getGrainsBuilder(map, toLocalDate(e.getDate())).wheat(e.getClose()).wheatVolume(e.getVolume()));
        cornRepository.findTop30ByOrderByDateDesc().forEach(e ->
                getGrainsBuilder(map, toLocalDate(e.getDate())).corn(e.getClose()).cornVolume(e.getVolume()));
        coffeeRepository.findTop30ByOrderByDateDesc().forEach(e ->
                getGrainsBuilder(map, toLocalDate(e.getDate())).coffee(e.getClose()).coffeeVolume(e.getVolume()));
        sugarRepository.findTop30ByOrderByDateDesc().forEach(e ->
                getGrainsBuilder(map, toLocalDate(e.getDate())).sugar(e.getClose()).sugarVolume(e.getVolume()));

        return map.entrySet().stream()
                .sorted(Map.Entry.<LocalDate, GrainsDto.GrainsDtoBuilder>comparingByKey().reversed())
                .map(entry -> entry.getValue().date(java.sql.Date.valueOf(entry.getKey())).build())
                .collect(Collectors.toList());
    }

    // 3. 원자재 30개 (CommoditiesDto) -> CommoditiesDto는 java.sql.Date 사용
    public List<CommoditiesDto> getLatest30CommoditiesDto() {
        Map<LocalDate, CommoditiesDto.CommoditiesDtoBuilder> map = new HashMap<>();

        goldRepository.findTop30ByOrderByDateDesc().forEach(e ->
                getCommoditiesBuilder(map, toLocalDate(e.getDate())).gold(e.getClose()).goldVolume(e.getVolume()));
        silverRepository.findTop30ByOrderByDateDesc().forEach(e ->
                getCommoditiesBuilder(map, toLocalDate(e.getDate())).silver(e.getClose()).silverVolume(e.getVolume()));
        copperRepository.findTop30ByOrderByDateDesc().forEach(e ->
                getCommoditiesBuilder(map, toLocalDate(e.getDate())).copper(e.getClose()).copperVolume(e.getVolume()));
        crudeOilRepository.findTop30ByOrderByDateDesc().forEach(e ->
                getCommoditiesBuilder(map, toLocalDate(e.getDate())).crudeOil(e.getClose()).crudeOilVolume(e.getVolume()));
        brentOilRepository.findTop30ByOrderByDateDesc().forEach(e ->
                getCommoditiesBuilder(map, toLocalDate(e.getDate())).brentOil(e.getClose()).brentOilVolume(e.getVolume()));

        return map.entrySet().stream()
                .sorted(Map.Entry.<LocalDate, CommoditiesDto.CommoditiesDtoBuilder>comparingByKey().reversed())
                .map(entry -> entry.getValue().date(java.sql.Date.valueOf(entry.getKey())).build())
                .collect(Collectors.toList());
    }

    // 4. 지수 30개 (CommoditiesIndexDto) -> CommoditiesIndexDto는 java.sql.Date 사용
    public List<CommoditiesIndexDto> getLatest30CommoditiesIndexDto() {
        Map<LocalDate, CommoditiesIndexDto.CommoditiesIndexDtoBuilder> map = new HashMap<>();

        dxyRepository.findTop30ByOrderByDateDesc().forEach(e ->
                getCommoditiesIndexBuilder(map, toLocalDate(e.getDate())).dxy(e.getClose()));
        vixRepository.findTop30ByOrderByDateDesc().forEach(e ->
                getCommoditiesIndexBuilder(map, toLocalDate(e.getDate())).vix(e.getClose()));

        return map.entrySet().stream()
                .sorted(Map.Entry.<LocalDate, CommoditiesIndexDto.CommoditiesIndexDtoBuilder>comparingByKey().reversed())
                .map(entry -> entry.getValue().date(java.sql.Date.valueOf(entry.getKey())).build())
                .collect(Collectors.toList());
    }

    // 5. 주식 30개 (StockDto) -> StockDto는 java.sql.Date 사용
    public List<StockDto> getLatest30StockDto() {
        Map<LocalDate, StockDto.StockDtoBuilder> map = new HashMap<>();

        sp500Repository.findTop30ByOrderByDateDesc().forEach(e ->
                getStockBuilder(map, toLocalDate(e.getDate())).sp500(e.getClose()).sp500Volume(e.getVolume()));
        dowJonesRepository.findTop30ByOrderByDateDesc().forEach(e ->
                getStockBuilder(map, toLocalDate(e.getDate())).dowJones(e.getClose()).dowJonesVolume(e.getVolume()));
        nasdaqRepository.findTop30ByOrderByDateDesc().forEach(e ->
                getStockBuilder(map, toLocalDate(e.getDate())).nasdaq(e.getClose()).nasdaqVolume(e.getVolume()));
        kospiRepository.findTop30ByOrderByDateDesc().forEach(e ->
                getStockBuilder(map, toLocalDate(e.getDate())).kospi(e.getClose()).kospiVolume(e.getVolume()));
        kosdaqRepository.findTop30ByOrderByDateDesc().forEach(e ->
                getStockBuilder(map, toLocalDate(e.getDate())).kosdaq(e.getClose()).kosdaqVolume(e.getVolume()));

        // **수정된 부분**: StockDto의 date 필드는 java.sql.Date 타입이므로 변환(valueOf)이 필요함
        return map.entrySet().stream()
                .sorted(Map.Entry.<LocalDate, StockDto.StockDtoBuilder>comparingByKey().reversed())
                .map(entry -> entry.getValue().date(java.sql.Date.valueOf(entry.getKey())).build())
                .collect(Collectors.toList());
    }


    // ================= Helper Methods =================

    // java.util.Date -> java.time.LocalDate 변환
    private LocalDate toLocalDate(java.util.Date date) {
        if (date == null) return null;
        return date.toInstant().atZone(ZoneId.systemDefault()).toLocalDate();
    }

    // Exchange Builder Helper
    private ExchangeDto.ExchangeDtoBuilder getBuilder(Map<LocalDate, ExchangeDto.ExchangeDtoBuilder> map, LocalDate date) {
        return map.computeIfAbsent(date, d -> ExchangeDto.builder().date(d)); // ExchangeDto는 LocalDate 사용
    }

    // Grains Builder Helper
    private GrainsDto.GrainsDtoBuilder getGrainsBuilder(Map<LocalDate, GrainsDto.GrainsDtoBuilder> map, LocalDate date) {
        return map.computeIfAbsent(date, d -> GrainsDto.builder());
    }

    // Commodities Builder Helper
    private CommoditiesDto.CommoditiesDtoBuilder getCommoditiesBuilder(Map<LocalDate, CommoditiesDto.CommoditiesDtoBuilder> map, LocalDate date) {
        return map.computeIfAbsent(date, d -> CommoditiesDto.builder());
    }

    // Index Builder Helper
    private CommoditiesIndexDto.CommoditiesIndexDtoBuilder getCommoditiesIndexBuilder(Map<LocalDate, CommoditiesIndexDto.CommoditiesIndexDtoBuilder> map, LocalDate date) {
        return map.computeIfAbsent(date, d -> CommoditiesIndexDto.builder());
    }

    // Stock Builder Helper
    private StockDto.StockDtoBuilder getStockBuilder(Map<LocalDate, StockDto.StockDtoBuilder> map, LocalDate date) {
        return map.computeIfAbsent(date, d -> StockDto.builder());
    }

    // DTO 변환 메서드 (Mental)
    private ConsumerSentimentDto toConsumerSentimentDto(ConsumerSentiment entity) {
        ConsumerSentimentDto dto = new ConsumerSentimentDto();
        dto.setDate(entity.getDate());
        dto.setStatCode(entity.getStatCode());
        dto.setItemCode(entity.getItemCode());
        dto.setItemName(entity.getItemName());
        dto.setUnitName(entity.getUnitName());
        dto.setValue(entity.getValue());
        dto.setRegionCode(entity.getRegionCode());
        dto.setRegionName(entity.getRegionName());
        return dto;
    }

    private EconomicSentimentDto toEconomicSentimentDto(EconomicSentiment entity) {
        EconomicSentimentDto dto = new EconomicSentimentDto();
        dto.setDate(entity.getDate());
        dto.setStatCode(entity.getStatCode());
        dto.setItemCode(entity.getItemCode());
        dto.setItemName(entity.getItemName());
        dto.setUnitName(entity.getUnitName());
        dto.setValue(entity.getValue());
        return dto;
    }

    private NewsSentimentDto toNewsSentimentDto(NewsSentiment entity) {
        NewsSentimentDto dto = new NewsSentimentDto();
        dto.setDate(entity.getDate());
        dto.setStatCode(entity.getStatCode());
        dto.setItemCode(entity.getItemCode());
        dto.setItemName(entity.getItemName());
        dto.setUnitName(entity.getUnitName());
        dto.setValue(entity.getValue());
        return dto;
    }
}