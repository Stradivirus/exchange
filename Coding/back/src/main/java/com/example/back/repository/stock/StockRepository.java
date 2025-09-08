package com.example.back.repository.stock;

import com.example.back.entity.stock.Stock;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.sql.Date;
import java.util.List;

@Repository
public interface StockRepository extends JpaRepository<Stock, Date> {
    List<Stock> findTop30ByOrderByDateDesc();
}
