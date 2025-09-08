package com.example.back.repository.commodities_index;

import com.example.back.entity.commodities_index.CommoditiesIndex;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.time.LocalDate;
import java.util.List;

@Repository
public interface CommoditiesIndexRepository extends JpaRepository<CommoditiesIndex, LocalDate> {
    List<CommoditiesIndex> findTop30ByOrderByDateDesc();
}