
package com.example.back.dto;

import com.example.back.dto.grains.*;
import com.example.back.dto.commodities.*;
import com.example.back.dto.commodities_index.*;
import com.example.back.dto.exchange.*;
import com.example.back.dto.interest.*;
import com.example.back.dto.stock.*;
import java.util.List;

import lombok.*;

@Getter
@Setter
@NoArgsConstructor
@AllArgsConstructor
@Builder
public class MainPageResponseDto {
    // 곡물 상세 리스트
    private List<RiceDto> riceList;
    private List<WheatDto> wheatList;
    private List<CornDto> cornList;
    private List<CoffeeDto> coffeeList;
    private List<SugarDto> sugarList;

    // 주요 원자재 상세 리스트
    private List<GoldDto> goldList;
    private List<SilverDto> silverList;
    private List<CopperDto> copperList;
    private List<CrudeOilDto> crudeOilList;
    private List<BrentOilDto> brentOilList;

    // 주요 지수 상세 리스트
    private List<DxyDto> dxyList;
    private List<VixDto> vixList;

    // 환율 상세 리스트
    private List<UsdDto> usdList;
    private List<JpyDto> jpyList;
    private List<EurDto> eurList;
    private List<CnyDto> cnyList;

    // 금리 상세 리스트
    private List<KorBaseRateDto> korBaseRateList;
    private List<UsFedRateDto> usFedRateList;

    // 주가지수 상세 리스트
    private List<Sp500Dto> sp500List;
    private List<DowJonesDto> dowJonesList;
    private List<NasdaqDto> nasdaqList;
    private List<KospiDto> kospiList;
    private List<KosdaqDto> kosdaqList;
}
