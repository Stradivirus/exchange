package com.example.back.mongo.grains;

import org.springframework.data.mongodb.repository.MongoRepository;
import java.util.List; // 필수 추가

public interface WheatRepository extends MongoRepository<Wheat, String> {
    Wheat findTopByOrderByDateDesc();

    List<Wheat> findTop30ByOrderByDateDesc();

}
